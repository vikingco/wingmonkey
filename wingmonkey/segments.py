from marshmallow import fields

from wingmonkey.enums import SegmentFieldTypes
from wingmonkey.mailchimp_session import MailChimpSessionSchema
from wingmonkey.mailchimp_base import MailChimpData


class SegmentSerializer(MailChimpSessionSchema):

    id = fields.Int()
    name = fields.Str()
    member_count = fields.Int()
    type = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    options = fields.Dict()
    list_id = fields.Str()
    _links = fields.List(cls_or_instance=fields.Dict())

    def create(self, list_id, segment_instance):
        """
        :param list_id: id of list the segment will be added to
        :param segment_instance : Segment : segment to be created on server
        :return: Segment instance
        """
        self.exclude = segment_instance.empty_fields
        self._update_fields()

        response = self.session.post(f'lists/{list_id}/segments', json=self.dumps(segment_instance).data)
        self.exclude = ()
        self._update_fields()
        if response:
            return Segment(**self.load(response.json()).data)

    def read(self, list_id, segment_id):
        """
        :param list_id: id of list the segment is defined for
        :param segment_id: id of the segment
        :return: Segment instance
        """

        response = self.session.get(f'lists/{list_id}/segments/{segment_id}')
        return Segment(**self.load(response.json()).data)

    def update(self, list_id, segment_instance):
        """
        :param list_id: id of list the segment will be updated in
        :param segment_instance: Segment
        :return: updated Segment instance on server
        """
        self.only = ('name', 'options')
        self._update_fields()

        response = self.session.patch(f'lists/{list_id}/segments/{segment_instance.id}',
                                      json=self.dumps(segment_instance).data)
        self.only = ()
        self._update_fields()
        if response:
            return Segment(**self.load(response.json()).data)

    def delete(self, list_id, segment_id):
        """
        :param list_id: id of list the segment will be deleted from
        :param merge_id: id of segment to delete
        :return: boolean
        """
        if self.session.delete(f'lists/{list_id}/segments/{segment_id}'):
            return True


class Segment(MailChimpData):

    def __init__(self, id=None, name=None, member_count=0, type=SegmentFieldTypes.SAVED, created_at=None,
                 updated_at=None, options=None, list_id=None, _links=None):

        self.id = id
        self.name = name
        self.member_count = member_count
        self.type = type
        self.created_at = created_at
        self.updated_at = updated_at
        self.options = options
        self.list_id = list_id
        self._links = _links


class SegmentCollectionSerializer(MailChimpSessionSchema):

    segments = fields.List(cls_or_instance=fields.Nested(SegmentSerializer))
    list_id = fields.Str()
    total_items = fields.Int()
    _links = fields.List(cls_or_instance=fields.Dict())

    def read(self, list_id):
        """
        :param list_id: id of list the segments are defined for
        :return: SegmentsCollection
        """

        response = self.session.get(f'lists/{list_id}/segments')
        return SegmentCollection(**self.load(response.json()).data)


class SegmentCollection(MailChimpData):

    def __init__(self, segments=None, list_id=None, total_items=0, _links=None):

        self.segments = segments
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links
