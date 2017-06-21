from wingmonkey.serializers import Serializer
from wingmonkey.mailchimp_session import MailChimpSession


class MailChimpAccountInfo(Serializer):

    def __init__(self, account_id=None, login_id=None, account_name=None, email=None, first_name=None, last_name=None,
                 username=None, role=None, contact=None, total_subscribers=0):
        """
        class representing mailchimp account info
        :param account_id: 
        :param login_id: 
        :param account_name: 
        :param email: 
        :param first_name: 
        :param last_name: 
        :param username: 
        :param role: 
        :param contact: 
        :param total_subscribers: 
        """
        self.account_id = account_id
        self.login_id = login_id
        self.account_name = account_name
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.role = role
        self.contact = contact
        self.total_subscribers = total_subscribers

        self.deserialize(MailChimpSession().get().text)
