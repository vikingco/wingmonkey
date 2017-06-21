from logging import getLogger

from requests import Session, exceptions
from requests.auth import HTTPBasicAuth

from wingmonkey.settings import MAILCHIMP_ROOT, MAILCHIMP_API_KEY

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
            raise ClientException(response.status_code, response.content)
        except exceptions.Timeout:
            raise ClientException(504, 'Time out')
        except exceptions.ConnectionError:
            raise ClientException(503, 'Can not connect to server')

    def get(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.get, url, json, query_parameters)

    def post(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.post, url, json, query_parameters)

    def patch(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.patch, url, json, query_parameters)

    def delete(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.delete, url, json, query_parameters)


class ClientException(Exception):
    """
    Exception indicating an unexpected http response was received. (not 2xx and not 404)
    """
    def __init__(self, http_code, response_body):
        self.http_code = http_code
        self.response_body = response_body
        logger.error(response_body)

    def __str__(self):
        return '{}: {}'.format(self.http_code, self.response_body)
