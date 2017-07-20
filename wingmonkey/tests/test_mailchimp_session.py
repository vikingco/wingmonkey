from requests_mock import Mocker
from requests.exceptions import Timeout, ConnectionError
from json import dumps
from pytest import raises, fixture

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
