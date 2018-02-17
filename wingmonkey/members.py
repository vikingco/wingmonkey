from hashlib import md5

from logging import getLogger
from marshmallow import fields

from wingmonkey.mailchimp_session import ClientException, MailChimpSessionSchema
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.enums import MemberStatus

logger = getLogger(__name__)


class MemberSerializer(MailChimpSessionSchema):
    """
    class representing member schema in mailchimp
    inherits from marshmallow Schema https://marshmallow.readthedocs.io/en/latest/quickstart.html#declaring-schemas
    """

    id = fields.Str()
    email_address = fields.Str()
    unique_email_id = fields.Email()
    email_type = fields.Str()
    status = fields.Str()
    unsubscribe_reason = fields.Str()
    unsubscribe_campaign_id = fields.Str()
    unsubscribe_campaign_title = fields.Str()
    merge_fields = fields.Dict()
    interests = fields.Dict()
    stats = fields.Dict()
    ip_signup = fields.Str()
    timestamp_signup = fields.Str()
    ip_opt = fields.Str()
    timestamp_opt = fields.Str()
    member_rating = fields.Int()
    last_changed = fields.Str()
    language = fields.Str()
    vip = fields.Boolean()
    email_client = fields.Str()
    location = fields.Dict()
    last_note = fields.Dict()
    list_id = fields.Str()
    _links = fields.List(cls_or_instance=fields.Dict())

    def create(self, list_id, instance):
        """
        :param list id: str: id of list to add this member to
        :param instance: Member:  instance to be created on server
        :return: Member:  instance created on mailchimp server
        """
        self.exclude = instance.empty_fields
        self._update_fields()

        response = self.session.post(f'lists/{list_id}/members', json=self.dumps(instance).data)
        self.exclude = ()
        self._update_fields()
        if response:
            return Member(**self.load(response.json()).data)

    def read(self, list_id, member_id=None, query=None):
        """
        :param list_id: str: List id
        :param member_id: str: Member id
        :param query: dict: query parameters
        :return: Member instance
        """
        # If no id is given we'll get the first member of the first list we find on the server
        if member_id is None:
            try:
                member_id = self.session.get(f'lists/{list_id}/members',
                                             query_parameters=query).json()['members'][0]['id']
            except IndexError:
                logger.warning('No members found for list %s', list_id)
                return

        response = self.session.get(f'lists/{list_id}/members/{member_id}', query_parameters=query)
        return Member(**self.load(response.json()).data)

    def update(self, list_id, instance, query=None):
        """
        :param list_id: str: List id
        :param instance: Member
        :param query: dict: query parameters
        :return: updated Member Instance
        """
        # limit serializer to fields that are accepted as PATCH parameters
        self.only = ('email_address', 'email_type', 'status', 'merge_fields', 'interests', 'language', 'vip',
                     'location')
        self._update_fields()

        response = self.session.patch(f'lists/{list_id}/members/{instance.id}', json=self.dumps(instance).data,
                                      query_parameters=query)
        self.only = ()
        self._update_fields()
        if response:
            return Member(**self.load(response.json()).data)

    def delete(self, list_id, member_id):
        if self.session.delete(f'lists/{list_id}/members/{member_id}'):
            return True


class Member(MailChimpData):

    __slots__ = ('id', 'email_address', 'unique_email_id', 'email_type', 'status', 'unsubscribe_reason',
                 'unsubscribe_campaign_id', 'unsubscribe_campaign_title', 'merge_fields', 'interests', 'stats',
                 'ip_signup', 'timestamp_signup', 'ip_opt', 'timestamp_opt', 'member_rating', 'last_changed',
                 'language', 'vip', 'email_client', 'location', 'last_note', 'list_id', '_links',
                 )

    def __init__(self, id=None, email_address=None, unique_email_id=None, email_type=None,
                 status=MemberStatus.SUBSCRIBED, unsubscribe_reason=None, unsubscribe_campaign_id=None,
                 unsubscribe_campaign_title=None, merge_fields=None, interests=None, stats=None, ip_signup=None,
                 timestamp_signup=None, ip_opt=None, timestamp_opt=None, member_rating=None, last_changed=None,
                 language='en', vip=False, email_client=None, location=None, last_note=None, list_id=None, _links=None):

        self.id = id
        self.email_address = email_address
        self.unique_email_id = unique_email_id
        self.email_type = email_type
        self.status = status
        self.unsubscribe_reason = unsubscribe_reason
        self.unsubscribe_campaign_id = unsubscribe_campaign_id
        self.unsubscribe_campaign_title = unsubscribe_campaign_title
        self.merge_fields = self._format_merge_fields(merge_fields)
        self.interests = interests
        self.stats = stats
        self.ip_signup = ip_signup
        self.timestamp_signup = timestamp_signup
        self.ip_opt = ip_opt
        self.timestamp_opt = timestamp_opt
        self.member_rating = member_rating
        self.last_changed = last_changed
        self.language = language
        self.vip = vip
        self.email_client = email_client
        self.location = location
        self.last_note = last_note
        self.list_id = list_id
        self._links = _links

    @staticmethod
    def _format_merge_fields(merge_fields):
        if merge_fields is None:
            return {}
        for key, value in merge_fields.items():
            if value is None:
                merge_fields[key] = ''
        return merge_fields


class MemberCollectionSerializer(MailChimpSessionSchema):

    members = fields.List(cls_or_instance=fields.Nested(MemberSerializer))
    list_id = fields.Str()
    total_items = fields.Int()
    _links = fields.List(cls_or_instance=fields.Dict())

    def read(self, list_id, query=None):
        """
        :param list_id: str: List id
        :param query: dict: query parameters
        :return: Members instance
        """
        response = self.session.get(f'lists/{list_id}/members', query_parameters=query)
        return MemberCollection(**self.load(response.json()).data)


class MemberCollection(MailChimpData):

    def __init__(self, members=None, list_id=None, total_items=0, _links=None):

        self.members = members
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links


class MemberBatchRequestSerializer(MailChimpSessionSchema):

    members = fields.List(cls_or_instance=fields.Nested(MemberSerializer, only=('email_address', 'status',
                                                                                'merge_fields', 'language')))
    update_existing = fields.Boolean()

    def create(self, list_id, member_batch_request_instance):

        response = self.session.post(f'lists/{list_id}', json=self.dumps(member_batch_request_instance).data)
        if response:
            return MemberBatchResponse(
                **MemberBatchResponseSerializer(session=self.session).load(response.json()).data)


class MemberBatchRequest(MailChimpData):

    def __init__(self, members, update_existing=True):
        """

        :param members: List: list of Member instances
        :param update_existing: Bool: update existing members in list
        """

        if len(members) > 500:
            raise ClientException(0, 'max 500 members are supported in a batch request')

        self.members = members
        self.update_existing = update_existing


class MemberBatchResponseSerializer(MailChimpSessionSchema):

    new_members = fields.List(cls_or_instance=fields.Nested(MemberSerializer))
    updated_members = fields.List(cls_or_instance=fields.Nested(MemberSerializer))
    errors = fields.List(cls_or_instance=fields.Dict())
    total_created = fields.Int()
    total_updated = fields.Int()
    error_count = fields.Int()
    _links = fields.List(cls_or_instance=fields.Dict())


class MemberBatchResponse(MailChimpData):

    def __init__(self, new_members=None, updated_members=None, errors=None, total_created=0, total_updated=0,
                 error_count=0, _links=None):

        self.new_members = new_members
        self.updated_members = updated_members
        self.errors = errors
        self.total_created = total_created
        self.total_updated = total_updated
        self.error_count = error_count
        self._links = _links


class MemberActivitySerializer(MailChimpSessionSchema):

    activity = fields.List(cls_or_instance=fields.Dict())
    email_id = fields.Str()
    list_id = fields.Str()
    total_items = fields.Int()
    _links = fields.List(cls_or_instance=fields.Dict())

    def read(self, list_id, email_address, query=None):
        subscriber_hash = generate_member_id(email_address)
        response = self.session.get(f'lists/{list_id}/members/{subscriber_hash}/activity', query_parameters=query)
        return MemberActivity(**self.load(response.json()).data)


class MemberActivity(MailChimpData):
    def __init__(self, activity=None, email_id=None, list_id=None, total_items=0, _links=None):

        self.activity = activity
        self.email_id = email_id
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links


def generate_member_id(email_address):
    # handle None values
    if not email_address:
        return

    member_hash = md5()
    member_hash.update(email_address.lower().encode())
    return member_hash.hexdigest()
