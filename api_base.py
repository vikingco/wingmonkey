from requests import Session, exceptions
from requests.auth import HTTPBasicAuth
from logging import getLogger

from settings import MAILCHIMP_ROOT, MAILCHIMP_API_KEY
from helpers import SerializerMixin

logger = getLogger(__name__)


class MailChimpSession:
    """
    class representing a mailchimp api session and it's available methods
    """

    def __init__(self):

        self.auth = HTTPBasicAuth('mailchimpuser', MAILCHIMP_API_KEY)
        self.session = Session()

    def _request(self, method, url=None, json=None, query_parameters=None):
        """
        
        :param method: HTTPrequest method 
        :param url: url for the request
        :param json: json data
        :param query_parameters: query parameters for get request
        :return: 
        """

        if not url:
            url = ''

        try:
            logger.debug('%s : %s/%s json=%s param=%s', method, MAILCHIMP_ROOT, url, json, query_parameters)
            response = method('{}/{}'.format(MAILCHIMP_ROOT, url), headers={'Accept': 'application/json'},
                              data=json, params=query_parameters, auth=self.auth)

            response.raise_for_status()
            return response
        except exceptions.HTTPError:
            logger.error('STATUS %s %s', response.status_code, response.content)
        except exceptions.Timeout:
            logger.error('STATUS 504 Time out')
        except exceptions.ConnectionError:
            logger.error('STATUS 503 Can not connect to server')

    def get(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.get, url, json, query_parameters)

    def post(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.post, url, json, query_parameters)

    def patch(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.patch, url, json, query_parameters)

    def delete(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.delete, url, json, query_parameters)


class MailChimpAccountInfo(SerializerMixin):

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

