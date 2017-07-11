from logging import getLogger
from asyncio import get_event_loop, TimeoutError

from requests import Session, exceptions
from requests.auth import HTTPBasicAuth

from aiohttp import ClientSession, web_exceptions, client_exceptions, BasicAuth
from aiohttp.connector import TCPConnector


from wingmonkey.settings import MAILCHIMP_ROOT, MAILCHIMP_API_KEY

logger = getLogger(__name__)
loop = get_event_loop()


class MailChimpSession(object):
    """
    class representing a mailchimp api session and it's available methods
    """

    def __init__(self, api_endpoint=MAILCHIMP_ROOT):

        self.api_endpoint = api_endpoint

        # regular requests session
        self.session = Session()
        # async aiohttp session
        connector = TCPConnector(loop=loop)
        self.async_session = ClientSession(connector=connector)

    def __del__(self):
        self.session.close()
        self.async_session.close()

    def _request(self, method, url=None, json=None, query_parameters=None, stream=False):
        """
        :param method: HTTPrequest method
        :param url: url for the request
        :param json: json data
        :param query_parameters: dict: query parameters for get request
        :return:
        """
        auth = HTTPBasicAuth('mailchimpuser', MAILCHIMP_API_KEY)

        if not url:
            url = ''

        try:
            logger.warning('%s : %s/%s json=%s param=%s', method, self.api_endpoint, url, json, query_parameters)
            response = method('{}/{}'.format(self.api_endpoint, url), headers={'Accept': 'application/json'},
                              data=json, params=query_parameters, auth=auth, stream=stream)
            response.raise_for_status()
            return response
        except exceptions.HTTPError:
            raise ClientException(response.status_code, response.content)
        except exceptions.Timeout:
            raise ClientException(504, 'Time out')
        except exceptions.ConnectionError:
            raise ClientException(503, 'Can not connect to server')

    async def _async_request(self, method, url=None, json=None, query_parameters=None):
        """

        :param method: HTTPrequest method
        :param url: url for the request
        :param json: json data
        :param query_parameters: dict: query parameters for get request
        :return:
        """

        auth = BasicAuth('mailchimpuser', MAILCHIMP_API_KEY)

        if not url:
            url = ''

        try:
            logger.warning('%s : %s/%s json=%s param=%s', method, self.api_endpoint, url, json, query_parameters)
            response = await method('{}/{}'.format(self.api_endpoint, url), headers={'Accept': 'application/json'},
                                    data=json, params=query_parameters, auth=auth)

            response.raise_for_status()
            return response
        except web_exceptions.HTTPError:
            raise ClientException(response.status_code, response.content.read_nowait())
        except client_exceptions.ClientResponseError as e:
            raise ClientException(e.code, response.content.read_nowait())
        except web_exceptions.HTTPRequestTimeout:
            raise ClientException(504, 'Time out')
        except web_exceptions.HTTPServiceUnavailable:
            raise ClientException(503, 'Can not connect to server')
        except TimeoutError:
            raise ClientException(0, 'Asyncio Timeout Error')

    async def async_get(self, url=None, json=None, query_parameters=None):
        response = await self._async_request(self.async_session.get, url, json, query_parameters)
        return await response.json()

    async def async_post(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.post, url, json, query_parameters)

    async def async_patch(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.patch, url, json, query_parameters)

    async def async_delete(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.delete, url, json, query_parameters)

    def get(self, url=None, json=None, query_parameters=None, stream=False, async_request=False):
        if async_request:
            return loop.run_until_complete(self.async_get(url, json, query_parameters))
        return self._request(self.session.get, url=url, json=json, query_parameters=query_parameters, stream=stream)

    def post(self, url=None, json=None, query_parameters=None, async_request=False):
        if async_request:
            return loop.run_until_complete(self.async_post(url, json, query_parameters))
        return self._request(self.session.post, url=url, json=json, query_parameters=query_parameters)

    def patch(self, url=None, json=None, query_parameters=None, async_request=False):
        if async_request:
            return loop.run_until_complete(self.async_patch(url, json, query_parameters))
        return self._request(self.session.patch, url=url, json=json, query_parameters=query_parameters)

    def delete(self, url=None, json=None, query_parameters=None, async_request=False):
        if async_request:
            return loop.run_until_complete(self.async_delete(url, json, query_parameters))
        return self._request(self.session.delete, url=url, json=json, query_parameters=query_parameters)


class ClientException(Exception):
    """
    Exception indicating an unexpected http response was received. (not 2xx and not 404)
    """
    def __init__(self, http_code, response_body):
        self.http_code = http_code
        self.response_body = response_body
        logger.error(response_body)

    def __repr__(self):
        return '{}: {}'.format(self.http_code, self.response_body)
