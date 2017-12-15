from logging import getLogger
from marshmallow import fields

from wingmonkey.mailchimp_session import MailChimpSessionSchema
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.enums import VISIBILITY_PRIVATE, DEFAULT_RECORD_COUNT

from wingmonkey.settings import DEFAULT_PERMISSION_REMINDER, CAMPAIGN_DEFAULTS, DEFAULT_CONTACT

logger = getLogger(__name__)


class ListSerializer(MailChimpSessionSchema):
    """
    class representing mailing list schema in mailchimp
    inherits from marshmallow Schema https://marshmallow.readthedocs.io/en/latest/quickstart.html#declaring-schemas
    """

    id = fields.Str()
    web_id = fields.Str()
    name = fields.Str()
    contact = fields.Dict(default=DEFAULT_CONTACT)
    permission_reminder = fields.Str(default=DEFAULT_PERMISSION_REMINDER)
    use_archive_bar = fields.Boolean(default=False)
    campaign_defaults = fields.Dict(default=CAMPAIGN_DEFAULTS)
    notify_on_subscribe = fields.Str()
    notify_on_unsubscribe = fields.Str()
    date_created = fields.DateTime()
    list_rating = fields.Str()
    email_type_option = fields.Boolean(default=False)
    subscribe_url_short = fields.Str()
    subscribe_url_long = fields.Str()
    beamer_address = fields.Str()
    visibility = fields.Str(default=VISIBILITY_PRIVATE)
    modules = fields.Str()
    stats = fields.Dict()
    _links = fields.List(cls_or_instance=fields.Dict())

    def create(self, instance):
        """
        create list on mailchimp server
        :return: MailChimpList instance
        """
        # Removing empty values before serialization (exclude option on schema) is useful when doing a post call
        # as we can not know the correct values of certain keys yet before creation on the API side( eg id ).
        # It also prevents unwanted overwriting.
        self.exclude = instance.empty_fields
        self._update_fields()

        response = self.session.post('lists', json=self.dumps(instance).data)
        self.exclude = ()
        self._update_fields()
        if response:
            return List(**self.load(response.json()).data)

    def read(self, list_id=None):
        """
        get list from mailchimp server and update object instance attributes
        :param list_id: id of List instance
        :return: updated MailChimpList instance
        """
        # If no id is given we'll get the first list we find on the server
        if list_id is None:
            try:
                list_id = self.session.get('lists').json()['lists'][0]['id']
            except IndexError:
                logger.warning('No lists found on server')
                return

        response = self.session.get(f'lists/{list_id}')
        return List(**self.load(response.json()).data)

    def update(self, instance):
        """
        :param instance: List instance
        :return: updated MailChimpList instance
        """
        self.only = ('name', 'contact', 'permission_reminder', 'use_archive_bar', 'campaign_defaults',
                     'notify_on_subscribe', 'email_type_option', 'visibility')
        self._update_fields()

        response = self.session.patch(f'lists/{instance.id}', json=self.dumps(instance).data)
        self.only = ()
        self._update_fields()
        if response:
            return List(**self.load(response.json()).data)

    def delete(self, instance):
        """
        delete list from mailchimp server
        :return: Bool
        """
        if self.session.delete(f'lists/{instance.id}'):
            return True


class List(MailChimpData):
    """
    class representing mailing list in mailchimp
    """

    def __init__(self, id=None, web_id=None, name=None, contact=DEFAULT_CONTACT,
                 permission_reminder=DEFAULT_PERMISSION_REMINDER, use_archive_bar=False,
                 campaign_defaults=CAMPAIGN_DEFAULTS, notify_on_subscribe=str(), notify_on_unsubscribe=str(),
                 date_created=None, list_rating=None, email_type_option=False, subscribe_url_short=None,
                 subscribe_url_long=None, beamer_address=None,  visibility=VISIBILITY_PRIVATE, modules=None, stats=None,
                 _links=None):

        self.id = id
        self.web_id = web_id
        self.name = name
        self.contact = contact
        self.permission_reminder = permission_reminder
        self.use_archive_bar = use_archive_bar
        self.campaign_defaults = campaign_defaults
        self.notify_on_subscribe = notify_on_subscribe
        self.notify_on_unsubscribe = notify_on_unsubscribe
        self.date_created = date_created
        self.list_rating = list_rating
        self.email_type_option = email_type_option
        self.subscribe_url_short = subscribe_url_short
        self.subscribe_url_long = subscribe_url_long
        self.beamer_address = beamer_address
        self.visibility = visibility
        self.modules = modules
        self.stats = stats
        self._links = _links


class ListCollectionSerializer(MailChimpSessionSchema):
    lists = fields.List(cls_or_instance=fields.Nested(ListSerializer))
    total_items = fields.Int()

    def read(self, count=DEFAULT_RECORD_COUNT, extra_parameters=None):
        query_parameters = dict(count=count)
        if extra_parameters:
            query_parameters.update(extra_parameters)
        response = self.session.get('lists', query_parameters=query_parameters)
        return ListCollection(**self.load(response.json()).data)


class ListCollection(MailChimpData):
    """
    class representing multiple mailchimp lists
    """

    def __init__(self, lists=None, total_items=0):

        self.lists = lists
        self.total_items = total_items


def get_all_lists(session=None):
    """
    Get all lists existing on mailchimp account
    :param session: MailChimpSession
    :return: ListCollection
    """
    list_collection_serializer = ListCollectionSerializer(session=session)

    # get list count
    list_count = list_collection_serializer.read(count=1, extra_parameters=dict(fields=['total_items'])).total_items

    # get all lists
    return list_collection_serializer.read(count=list_count)
