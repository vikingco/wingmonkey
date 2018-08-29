from logging import getLogger
from asyncio import get_event_loop, TimeoutError, CancelledError, new_event_loop, set_event_loop, wait_for
from requests import Session, exceptions
from requests.auth import HTTPBasicAuth
from aiohttp import ClientSession, web_exceptions, client_exceptions, BasicAuth
from aiohttp.connector import TCPConnector
from marshmallow import Schema

from wingmonkey.settings import (DEFAULT_MAILCHIMP_ROOT, DEFAULT_MAILCHIMP_API_KEY, MAILCHIMP_MAX_CONNECTIONS,
                                 DEFAULT_ASYNC_WAIT)

logger = getLogger(__name__)


class MailChimpSession(object):
    """
    class representing a mailchimp api session and it's available methods
    """

    def __init__(self, api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):

        self.api_endpoint = api_endpoint
        self.api_key = api_key

        if self.api_key == DEFAULT_MAILCHIMP_API_KEY:
            logger.info(f'{self.__class__} using default api key setting')

        # regular requests session
        self.session = Session()
        # async aiohttp session
        try:
            self.loop = get_event_loop()
        except RuntimeError:
            loop = new_event_loop()
            set_event_loop(loop)
            self.loop = loop

        connector = TCPConnector(loop=self.loop, verify_ssl=False, limit=MAILCHIMP_MAX_CONNECTIONS)
        self.async_session = ClientSession(connector=connector)

    def __del__(self):
        try:
            self.session.close()
            self.async_session.close()
        except Exception as e:
            logger.warning(f'MailChimpSession could not be closed cleanly: {e} ')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    def close(self):
        self.__del__()

    def _request(self, method, url=None, json=None, query_parameters=None, stream=False):
        """
        :param method: HTTPrequest method
        :param url: url for the request
        :param json: json data
        :param query_parameters: dict: query parameters for get request
        :param stream return stream response
        :return: HTTPresponse
        """
        auth = HTTPBasicAuth('mailchimpuser', self.api_key)

        if not url:
            url = ''

        try:
            logger.debug('%s : %s/%s json=%s param=%s', method, self.api_endpoint, url, json, query_parameters)
            response = method(f'{self.api_endpoint}/{url}', headers={'Accept': 'application/json'},
                              data=json, params=query_parameters, auth=auth, stream=stream, timeout=5*60)
            response.raise_for_status()
            return response
        except exceptions.HTTPError:
            raise ClientException(response.status_code, response.content)
        except exceptions.Timeout:
            raise ClientException(504, 'Time out')
        except exceptions.ConnectionError:
            raise ClientException(503, 'Can not connect to server')

    def get(self, url=None, json=None, query_parameters=None, stream=False):
        return self._request(self.session.get, url=url, json=json, query_parameters=query_parameters, stream=stream)

    def post(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.post, url=url, json=json, query_parameters=query_parameters)

    def patch(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.patch, url=url, json=json, query_parameters=query_parameters)

    def put(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.put, url=url, json=json, query_parameters=query_parameters)

    def delete(self, url=None, json=None, query_parameters=None):
        return self._request(self.session.delete, url=url, json=json, query_parameters=query_parameters)

    async def _async_request(self, method, url=None, json=None, query_parameters=None):
        """
        Method to make asynchronous requests (using aiohttp)
        :param method: HTTPrequest method
        :param url: url for the request
        :param json: json data
        :param query_parameters: dict: query parameters for get request
        :return: Coroutine
        """

        auth = BasicAuth('mailchimpuser', self.api_key)

        if not url:
            url = ''

        try:
            logger.debug('%s : %s/%s json=%s param=%s', method, self.api_endpoint, url, json, query_parameters)
            response = await wait_for(method(f'{self.api_endpoint}/{url}', headers={'Accept': 'application/json'},
                                      data=json, params=query_parameters, auth=auth), timeout=DEFAULT_ASYNC_WAIT)
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
        except (TimeoutError, client_exceptions.TimeoutError):
            raise ClientException(500, 'Asyncio timeout error')
        except CancelledError:
            raise ClientException(500, 'Asyncio future cancelled error')

    async def async_get(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.get, url, json, query_parameters)

    async def async_post(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.post, url, json, query_parameters)

    async def async_patch(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.patch, url, json, query_parameters)

    async def async_put(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.put, url, json, query_parameters)

    async def async_delete(self, url=None, json=None, query_parameters=None):
        return await self._async_request(self.async_session.delete, url, json, query_parameters)


class ClientException(Exception):
    """
    Exception indicating an unexpected http response was received. (not 2xx and not 404)
    """
    def __init__(self, http_code, response_body):
        self.status = http_code
        self.response_body = response_body if len(response_body) < 200 else f'{response_body[:200]}...TRUNCATED'

    def __repr__(self):
        return f'{self.status}: {self.response_body}'


class MailChimpSessionSchema(Schema):
    """
    Adds MailChimpSession to Schema
    When used as a nested object of another Schema it checks if a session already exists
    This to prevent initializing unneeded sessions
    """

    def __init__(self, session=None, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if session is None and self.context.get('session', None) is None:
            session = MailChimpSession()
        self.session = session
        self.context = {'session': session}
