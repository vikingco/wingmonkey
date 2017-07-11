from marshmallow import Schema, fields

from wingmonkey.enums import MergeFieldTypes
from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.mailchimp_base import MailChimpData

session = MailChimpSession()


class MergeFieldSerializer(Schema):

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

        response = session.post('lists/{}/merge-fields'.format(list_id), json=self.dumps(merge_field_instance).data)
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
        response = session.get('lists/{}/merge-fields/{}'.format(list_id, merge_id))
        return MergeField(**self.load(response.json()).data)

    def update(self, list_id, merge_field_instance):
        """
        :param list_id: id of list the merge field will be updated in 
        :param merge_field_instance: MergeField
        :return: updated MergeField instance on server
        """
        self.only = ('tag', 'name', 'required', 'default_value', 'public', 'display_order', 'options', 'help_text')
        self._update_fields()

        response = session.patch('lists/{}/merge-fields/{}'.format(list_id, merge_field_instance.merge_id),
                                 json=self.dumps(merge_field_instance).data)
        self.only = ()
        self._update_fields()
        if response:
            return MergeField(**self.load(response.json()).data)

    def delete(self, list_id, merge_id):
        """
        :param list_id: id of list the merge field will be deleted from
        :param merge_id: id of merge field to delete
        :return: boolean
        """
        if session.delete('lists/{}/merge-fields/{}'.format(list_id, merge_id)):
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


class MergeFieldsCollectionSerializer(Schema):

    merge_fields = fields.List(cls_or_instance=fields.Nested(MergeFieldSerializer))
    list_id = fields.Str()
    total_items = fields.Int()
    _links = fields.Dict()

    def read(self, list_id):
        """
        
        :param list_id: id of list the merge fields are defined for
        :return: MergeFieldsCollection
        """

        response = session.get('lists/{}/merge-fields'.format(list_id))
        return MergeFieldsCollection(**self.load(response.json()).data)


class MergeFieldsCollection(MailChimpData):

    def __init__(self, merge_fields=None, list_id=None, total_items=0, _links=None):

        self.merge_fields = merge_fields
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links
