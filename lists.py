from api_base import MailChimpSession
from settings import DEFAULT_PERMISSION_REMINDER, CAMPAIGN_DEFAULTS, DEFAULT_CONTACT
from helpers import SerializerMixin

session = MailChimpSession()


class List(SerializerMixin):
    """
    class representing mailing list in mailchimp
    """

    def __init__(self, id=None, web_id=None, name=None, contact=DEFAULT_CONTACT, permission_reminder=DEFAULT_PERMISSION_REMINDER,
                 use_archive_bar=False, campaign_defaults=CAMPAIGN_DEFAULTS, notify_on_subscribe=str(),
                 notify_on_unsubscribe=str(), date_created=None, list_rating=None, email_type_option=False,
                 subscribe_url_short=None, subscribe_url_long=None, beamer_address=None,  visibility='prv',
                 modules=None, stats=None, _links=None):

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

    def create(self):
        """
        create list on mailchimp server
        :return: updated MailChimpList instance
        """
        response = session.post('lists', json=self.serialize(strip_empty=True))
        if response:
            self.__dict__ = response.json()
            return self

    def read(self):
        """
        get list from mailchimp server and update object instance attributes
        :return: updated MailChimpList instance
        """
        # If this instance doesn't have an id yet we'll get the first list we find on the server
        if not self.id:
            list_id = session.get('lists').json()['lists'][0]['id']
        else:
            list_id = self.id

        json_string = session.get('lists/{}'.format(list_id)).text
        self.deserialize(json_string)
        return self

    def update(self):
        raise NotImplemented

    def delete(self):
        """
        delete list from mailchimp server
        :return: Bool
        """
        if session.delete('lists/{}'.format(self.id)):
            return True


class Lists(SerializerMixin):
    """
    class representing multiple mailchimp lists
    """

    def __init__(self, lists=None, total_items=0):

        self.lists = lists
        self.total_items = total_items

        self.deserialize(session.get('lists').text)

    @property
    def list_objects(self):
        """
        
        :return: list of all available mailing lists on server as List instances
        """
        all_lists = []
        for mailchimp_list in self.lists:
            all_lists.append(List(**mailchimp_list))
        return all_lists
