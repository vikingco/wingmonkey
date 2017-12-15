from marshmallow import fields

from wingmonkey.enums import MergeFieldTypes
from wingmonkey.mailchimp_session import MailChimpSessionSchema
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.lists import get_all_lists


class MergeFieldSerializer(MailChimpSessionSchema):

    merge_id = fields.Int()
    tag = fields.Str()
    name = fields.Str()
    type = fields.Str()
    required = fields.Boolean()
    default_value = fields.Str()
    public = fields.Boolean()
    display_order = fields.Int()
    options = fields.Dict()
    help_text = fields.Str()
    list_id = fields.Str()
    _links = fields.Dict()

    def create(self, list_id, merge_field_instance):
        """
        :param list_id: id of list the merge field will be defined for
        :param merge_field_instance: MergeField
        :return: MergeField instance created on server
        """
        self.exclude = merge_field_instance.empty_fields
        self._update_fields()

        response = self.session.post(f'lists/{list_id}/merge-fields', json=self.dumps(merge_field_instance).data)
        self.exclude = ()
        self._update_fields()
        if response:
            return MergeField(**self.load(response.json()).data)

    def read(self, list_id, merge_id):
        """
        :param list_id: id of list the merge field is defined for
        :param merge_id: id of merge field
        :return: MergeField instance found on server
        """
        response = self.session.get(f'lists/{list_id}/merge-fields/{merge_id}')
        return MergeField(**self.load(response.json()).data)

    def update(self, list_id, merge_field_instance):
        """
        :param list_id: id of list the merge field will be updated in
        :param merge_field_instance: MergeField
        :return: updated MergeField instance on server
        """
        self.exclude = merge_field_instance.empty_fields
        self._update_fields()

        response = self.session.patch(f'lists/{list_id}/merge-fields/{merge_field_instance.merge_id}',
                                      json=self.dumps(merge_field_instance).data)
        self.exclude = ()
        self._update_fields()
        if response:
            return MergeField(**self.load(response.json()).data)

    def delete(self, list_id, merge_id):
        """
        :param list_id: id of list the merge field will be deleted from
        :param merge_id: id of merge field to delete
        :return: boolean
        """
        if self.session.delete(f'lists/{list_id}/merge-fields/{merge_id}'):
            return True


class MergeField(MailChimpData):

    def __init__(self, merge_id=None, tag=None, name=None, type=MergeFieldTypes.TEXT, required=False,
                 default_value=None, public=False, display_order=None, options=None, help_text=None, list_id=None,
                 _links=None):
        self.merge_id = merge_id
        if not isinstance(tag, str):
            tag = str(tag)
        self.tag = tag.upper()[:10]  # to conform to format used by mailchimp
        self.name = name
        self.type = type
        self.required = required
        self.default_value = default_value
        self.public = public
        self.display_order = display_order
        self.options = options
        self.help_text = help_text
        self.list_id = list_id
        self._links = _links


class MergeFieldCollectionSerializer(MailChimpSessionSchema):

    merge_fields = fields.List(cls_or_instance=fields.Nested(MergeFieldSerializer))
    list_id = fields.Str()
    total_items = fields.Int()
    _links = fields.Dict()

    def read(self, list_id):
        """
        :param list_id: id of list the merge fields are defined for
        :return: MergeFieldsCollection
        """
        count = self._get_total_items_count(list_id)

        response = self.session.get(f'lists/{list_id}/merge-fields', query_parameters=dict(count=count))
        return MergeFieldCollection(**self.load(response.json()).data)

    def _get_total_items_count(self, list_id):
        """
        Get total amount of merge fields defined for given list
        :param list_id: id of list to get total item count for
        :return: int
        """

        response = self.session.get(f'lists/{list_id}/merge-fields', query_parameters=dict(count=1,
                                                                                           fields=['total_items']))
        return MergeFieldCollection(**self.load(response.json()).data).total_items


class MergeFieldCollection(MailChimpData):

    def __init__(self, merge_fields=None, list_id=None, total_items=0, _links=None):

        self.merge_fields = merge_fields
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links


def get_all_merge_fields(list_ids=None, session=None):
    """
    Get all merge fields for all lists
    :param list_ids: list : optional list of list ids, default is getting all mergefield for all lists
    :param session: Mailchimp Session to be used
    :return: MergeFieldCollection
    """
    if not list_ids:
        # get all lists
        list_collection = get_all_lists(session=session)
        list_ids = [l['id'] for l in list_collection.lists]
    else:
        list_ids = list_ids

    merge_field_collection_serializer = MergeFieldCollectionSerializer(session=session)

    all_merge_fields = MergeFieldCollection(merge_fields=[])

    for list_id in list_ids:
        merge_field_collection = merge_field_collection_serializer.read(list_id)
        for field in merge_field_collection.merge_fields:
            if not field['tag'] in [merge_field['tag'] for merge_field in all_merge_fields.merge_fields]:
                all_merge_fields.merge_fields.append(field)
    all_merge_fields.total_items = len(all_merge_fields.merge_fields)

    return all_merge_fields


def get_merge_field_mapping(merge_field_collection):
    """
    Return mapping dict of mergefield tags to names
    :param merge_field_collection: MergeFieldCollection
    :return: Dict
    """
    return {field['tag']: field['name'] for field in merge_field_collection.merge_fields}


def match_tag_to_name(name, mapping):
    """
    Try to match given name to mergefield tag defined in mapping dict
    Not case sensitive
    :param name: str
    :param mapping: dict
    :return: str: Tag
    """
    for tag, fieldname in mapping.items():
        if str(name).lower() == str(fieldname).lower():
            return tag
