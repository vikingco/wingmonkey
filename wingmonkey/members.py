from asyncio import get_event_loop, gather, Queue, sleep as async_sleep
from math import ceil
from time import sleep

from logging import getLogger
from marshmallow import Schema, fields

from wingmonkey.mailchimp_session import MailChimpSession, ClientException
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.enums import MemberStatus
from wingmonkey.lists import ListSerializer

logger = getLogger(__name__)
session = MailChimpSession()


class MemberSerializer(Schema):
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

        response = session.post('lists/{}/members'.format(list_id), json=self.dumps(instance).data)
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
                member_id = session.get('lists/{}/members'.format(list_id),
                                        query_parameters=query).json()['members'][0]['id']
            except IndexError:
                logger.warning('No members found for list %s', list_id)
                return

        response = session.get('lists/{}/members/{}'.format(list_id, member_id), query_parameters=query)
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

        response = session.patch('lists/{}/members/{}'.format(list_id, instance.id), json=self.dumps(instance).data,
                                 query_parameters=query)
        self.only = ()
        self._update_fields()
        if response:
            return Member(**self.load(response.json()).data)

    def delete(self, list_id, member_id):
        if session.delete('lists/{}/members/{}'.format(list_id, member_id)):
            return True


class Member(MailChimpData):

    def __init__(self, id=None, email_address=None, unique_email_id=None, email_type=None,
                 status=MemberStatus.SUBSCRIBED, unsubscribe_reason=None, unsubscribe_campaign_id=None,
                 unsubscribe_campaign_title=None, merge_fields=None, interests=None, stats=None, ip_signup=None,
                 ip_opt=None, timestamp_opt=None, member_rating=None, last_changed=None, language='en', vip=False,
                 email_client=None, location=None, last_note=None, list_id=None, _links=None):

        self.id = id
        self.email_address = email_address
        self.unique_email_id = unique_email_id
        self.email_type = email_type
        self.status = status
        self.unsubscribe_reason = unsubscribe_reason
        self.unsubscribe_campaign_id = unsubscribe_campaign_id
        self.unsubscribe_campaign_title = unsubscribe_campaign_title
        self.merge_fields = merge_fields
        self.interests = interests
        self.stats = stats
        self.ip_signup = ip_signup
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


class MembersCollectionSerializer(Schema):

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
        response = session.get('lists/{}/members'.format(list_id), query_parameters=query)
        return MembersCollection(**self.load(response.json()).data)


class MembersCollection(MailChimpData):

    def __init__(self, members=None, list_id=None, total_items=0, _links=None):

        self.members = members
        self.list_id = list_id
        self.total_items = total_items
        self._links = _links


async def _get_members_task(list_id, count, offset, extra_params=None, retry=3):
    query_parameters = dict(count=count, offset=offset)
    if extra_params:
        query_parameters.update(extra_params)

    while retry > 0:
        try:
            response = await session.async_get('lists/{}/members'.format(list_id),
                                               query_parameters=query_parameters)
            return response
        except ClientException as e:
            logger.warning('chunk for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            await async_sleep(5)


async def _get_chunk(queue, responses):
    while not queue.empty():
        params = await queue.get()
        responses.append(await _get_members_task(*params))


async def _get_all_members_async(queue, list_id, count, max_chunks, total_member_count=0, extra_params=None, retry=3):

    tasks = []
    responses = []

    for i in range(0, ceil(total_member_count / count)+1):
        queue.put_nowait([list_id, count, i * count, extra_params, retry])

    for chunk in range(1, max_chunks):
        tasks.append(_get_chunk(queue, responses))

    await gather(*tasks)
    return responses


def get_all_members_async(list_id, max_count=1000, max_chunks=9, extra_params=None, retry=3):
    # get list total member count
    while retry > 0:
        try:
            total_member_count = MembersCollectionSerializer().read(list_id, query=extra_params).total_items
        except ClientException as e:
            logger.warning('getting member count for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            sleep(5)
        else:
            count = _calculate_count(total_member_count, max_count, max_chunks)
            if count <= 0:
                return
            loop = get_event_loop()
            queue = Queue()
            return loop.run_until_complete(_get_all_members_async(queue=queue, list_id=list_id, count=count,
                                                                  max_chunks=max_chunks,
                                                                  total_member_count=total_member_count,
                                                                  extra_params=extra_params, retry=retry))


def _calculate_count(total_member_count, max_count, max_chunks):

    if (total_member_count / (max_count*max_chunks)) > 1:
        return max_count
    else:
        count = ceil(total_member_count/max_chunks)
        return count if count > 0 else 1
