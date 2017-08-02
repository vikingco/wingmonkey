from requests_mock import Mocker
from requests.exceptions import Timeout, ConnectionError
from json import dumps
from pytest import raises, fixture
from aioresponses import aioresponses

from wingmonkey.settings import MAILCHIMP_ROOT, MAILCHIMP_API_KEY
from wingmonkey.mailchimp_session import MailChimpSession, ClientException


@fixture
def mailchimp_session():
    return MailChimpSession()


def test_use_apikey_from_pytest_ini():
    assert MAILCHIMP_API_KEY == 'testingkey-test123'


def test_mailchimpsession_get(mailchimp_session):
    expected = 'Every day is caturday'

    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/miauw', text=expected)
        assert mailchimp_session.get('miauw')


def test_mailchimpsession_post(mailchimp_session):
    expected = dumps('{"posted":true}')

    def match_request_text(request):
        return expected in (request.text or '')

    with Mocker() as request_mock:
        request_mock.post(f'{MAILCHIMP_ROOT}/', additional_matcher=match_request_text)
        assert mailchimp_session.post(json=expected)


def test_mailchimpsession_patch(mailchimp_session):
    expected = dumps('{"posted":true}')

    def match_request_text(request):
        return expected in (request.text or '')

    with Mocker() as request_mock:
        request_mock.patch(f'{MAILCHIMP_ROOT}/', additional_matcher=match_request_text)
        assert mailchimp_session.patch(json=expected)


def test_mailchimpsession_delete(mailchimp_session):
    expected = dumps('{"posted":true}')

    def match_request_text(request):
        return expected in (request.text or '')

    with Mocker() as request_mock:
        request_mock.delete(f'{MAILCHIMP_ROOT}/', additional_matcher=match_request_text)
        assert mailchimp_session.delete(json=expected)


def test_mailchimpsession_get_params(mailchimp_session):
    expected = dict(question='everything', answer='42')
    expected_query_string = 'question=everything&answer=42'

    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/?{expected_query_string}', complete_qs=True)
        assert mailchimp_session.get(query_parameters=expected)


def test_mailchimpsession_post_params(mailchimp_session):
    expected = dict(question='everything', answer='42')
    expected_query_string = 'question=everything&answer=42'

    with Mocker() as request_mock:
        request_mock.post(f'{MAILCHIMP_ROOT}/?{expected_query_string}', complete_qs=True)
        assert mailchimp_session.post(query_parameters=expected)


def test_mailchimpsession_patch_params(mailchimp_session):
    expected = dict(question='everything', answer='42')
    expected_query_string = 'question=everything&answer=42'

    with Mocker() as request_mock:
        request_mock.patch(f'{MAILCHIMP_ROOT}/?{expected_query_string}', complete_qs=True)
        assert mailchimp_session.patch(query_parameters=expected)


def test_mailchimpsession_delete_params(mailchimp_session):
    expected = dict(question='everything', answer='42')
    expected_query_string = 'question=everything&answer=42'

    with Mocker() as request_mock:
        request_mock.delete(f'{MAILCHIMP_ROOT}/?{expected_query_string}', complete_qs=True)
        assert mailchimp_session.delete(query_parameters=expected)


def test_mailchimsession_http_exception(mailchimp_session):
    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', status_code=400)
        assert raises(ClientException, mailchimp_session.get)


def test_mailchimsession_time_out_exception(mailchimp_session):
    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', exc=Timeout)
        assert raises(ClientException, mailchimp_session.get)


def test_mailchimsession_connection_error_exception(mailchimp_session):
    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', exc=ConnectionError)
        assert raises(ClientException, mailchimp_session.get)


def test_client_exception_representation():
    exception = ClientException(400, 'Error Message')
    assert exception.__repr__() == '400: Error Message'


def test_mailchimp_session_async_get(mailchimp_session):
    expected = 'is caturday day Every'

    with aioresponses() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/miauw', payload=expected)
        response = mailchimp_session.loop.run_until_complete(mailchimp_session.async_get('miauw'))
        assert response == expected


def test_mailchimp_session_async_post(mailchimp_session):
    expected = dumps('{"posted":true}')
    with aioresponses() as request_mock:
        request_mock.post(f'{MAILCHIMP_ROOT}/', body=expected, payload='ok')
        response = mailchimp_session.loop.run_until_complete(mailchimp_session.async_post(json=expected))
        response_json = mailchimp_session.loop.run_until_complete(response.json())
        assert response_json == 'ok'


def test_mailchimp_session_async_patch(mailchimp_session):
    expected = dumps('{"patched":true}')
    with aioresponses() as request_mock:
        request_mock.patch(f'{MAILCHIMP_ROOT}/', body=expected, payload='ok')
        response = mailchimp_session.loop.run_until_complete(mailchimp_session.async_patch(json=expected))
        response_json = mailchimp_session.loop.run_until_complete(response.json())
        assert response_json == 'ok'


def test_mailchimp_session_async_delete(mailchimp_session):
    expected = dumps('{"deleted":true}')
    with aioresponses() as request_mock:
        request_mock.delete(f'{MAILCHIMP_ROOT}/', body=expected, payload='ok')
        response = mailchimp_session.loop.run_until_complete(mailchimp_session.async_delete(json=expected))
        response_json = mailchimp_session.loop.run_until_complete(response.json())
        assert response_json == 'ok'


def test_mailchimsession_async_http_exception(mailchimp_session):
    with aioresponses() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', status=400)
        assert raises(ClientException, mailchimp_session.loop.run_until_complete, mailchimp_session.async_get())


def test_mailchimsession_async_time_out_exception(mailchimp_session):
    with aioresponses() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', status=504)
        assert raises(ClientException, mailchimp_session.loop.run_until_complete, mailchimp_session.async_get())


def test_mailchimsession_async_client_connection_exception(mailchimp_session):
    with aioresponses() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/', status=503)
        assert raises(ClientException, mailchimp_session.loop.run_until_complete, mailchimp_session.async_get())
