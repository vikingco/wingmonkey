from copy import deepcopy
from datetime import datetime
from requests_mock import Mocker
from json import dumps, loads
from pytest import fixture
from aioresponses import aioresponses

from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.factories import MemberFactory
from wingmonkey.members import MemberSerializer
from wingmonkey.async_operations import get_all_members_async, batch_update_members_async, update_members_async
from wingmonkey.mailchimp_session import MailChimpSession


@fixture()
def expected_members():
    return {
        'members': [MemberSerializer().dumps(MemberFactory(list_id='ListyMcListface')).data for _ in range(100)],
        'list_id': 'ListyMcListface',
        'total_items': 100,
        '_links': None
    }


@fixture()
def expected_member_batches():
    members = [MemberFactory(list_id='ListyMcListface') for _ in range(1000)]

    batch1 = {
        'members': [loads(MemberSerializer(only=('email_address', 'status', 'merge_fields', 'language'))
                    .dumps(member).data) for member in members[0:500]],
        'update_existing': True
    }
    batch2 = {
        'members': [loads(MemberSerializer(only=('email_address', 'status', 'merge_fields', 'language'))
                    .dumps(member).data) for member in members[500:1000]],
        'update_existing': True

    }
    return batch1, batch2, members


@fixture()
def expected_members_with_custom_session():
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'
    session = MailChimpSession(api_endpoint=api_endpoint, api_key=api_key)
    return {
        'members': [MemberSerializer(session=session).dumps(MemberFactory(
            list_id='ListyMcListface')).data for _ in range(100)],
        'list_id': 'ListyMcListface',
        'total_items': 100,
        '_links': None
    }


@fixture()
def expected_batch_operation_resource():
    return {
        'id': 'wereallresources123',
        'status': 'pending',
        'total_operations': 1,
        'finished_operations': 0,
        'errored_operations': 0,
        'submitted_at': str(datetime.today()),
        'completed_at': None,
        'response_body_url': 'https://amailchimp/link/goes/here',
        '_links': None,
    }


def _create_chunks(members_dict, chunk_size):
    chunks = []
    for i in range(0, len(members_dict['members']), chunk_size):
        members_chunk = deepcopy(members_dict)
        members_chunk['members'] = members_chunk['members'][i:i + chunk_size]
        chunks.append(members_chunk)
    return chunks


def test_get_all_members_async(caplog, expected_members):
    """
    The function we test here calls another async function. This is the expected behaviour:
    First a regular get request should be  made to get total member count which will be mocked with Mocker
    Next we expect several aiohttp GET requests to get chunks of the member list which we will mock with aioresponses
    """

    with Mocker() as request_mock, aioresponses() as async_request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                         text=dumps({'total_items': 100}))
        # We will use max_count=10 which means 10 (100/10) async get tasks should be executed in this case
        chunks = _create_chunks(expected_members, chunk_size=10)
        for i in range(10):
            async_request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                                   body=dumps(chunks[i]))

        response = get_all_members_async(list_id=expected_members["list_id"], max_count=10)
        assert response.members == expected_members['members']

        # sanity check
        assert f'using default api key setting' in caplog.text


def test_get_all_members_async_exception(caplog, expected_members):
    """
    The function we test here calls another async function. This is the expected behaviour:
    First a regular get request should be  made to get total member count which will be mocked with Mocker
    Next we expect several aiohttp GET requests to get chunks of the member list which we will mock with aioresponses
    """
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with Mocker() as request_mock:
            request_mock.get(f'{api_endpoint}/lists/{expected_members["list_id"]}/members', status_code=400)

            assert not get_all_members_async(list_id=expected_members["list_id"], max_count=10, retry=1, sleepy_time=0,
                                             api_endpoint=api_endpoint, api_key=api_key)

            assert f'getting member count for list {expected_members["list_id"]} failed. Error' in caplog.text


def test_batch_update_members_async(caplog, expected_members, expected_batch_operation_resource):
    """
    Expected behaviour:
    The input list gets chopped up into chunks of 'members_per_call' length
    This should trigger list_length/members_per_call aiohttp POST requests that return batch operation resources
    """
    with aioresponses() as async_request_mock:
        # as the length of expected_members is 100 and we'll ask for 10 members per call there should be 10 requests
        for i in range(10):
            async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/batches', payload=expected_batch_operation_resource)

        response = batch_update_members_async(list_id=expected_members['list_id'],
                                              member_list=expected_members['members'], members_per_call=10)
        assert len(response) == 10
        for i in range(10):
            assert response[i].__dict__ == expected_batch_operation_resource

        # sanity check
        assert f'using default api key setting' in caplog.text


def test_get_all_members_async_with_custom_api_settings(caplog, expected_members_with_custom_session):
    """
    The function we test here calls another async function. This is the expected behaviour:
    First a regular get request should be  made to get total member count which will be mocked with Mocker
    Next we expect several aiohttp GET requests to get chunks of the member list which we will mock with aioresponses
    We use custom settings so no warning should have been logged
    """

    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with Mocker() as request_mock, aioresponses() as async_request_mock:
        request_mock.get(f'{api_endpoint}/lists/{expected_members_with_custom_session["list_id"]}/members',
                         text=dumps({'total_items': 100}))
        # We will use max_count=10 which means 10 (100/10) async get tasks should be executed in this case
        chunks = _create_chunks(expected_members_with_custom_session, chunk_size=10)
        for i in range(10):
            async_request_mock.get(f'{api_endpoint}/lists/{expected_members_with_custom_session["list_id"]}/members',
                                   body=dumps(chunks[i]))

        response = get_all_members_async(list_id=expected_members_with_custom_session["list_id"], max_count=10,
                                         api_endpoint=api_endpoint,
                                         api_key=api_key)
        assert response.members == expected_members_with_custom_session['members']
        assert f'using default api key setting' not in caplog.text


def test_batch_update_members_async_with_custom_api_settings(caplog, expected_members_with_custom_session,
                                                             expected_batch_operation_resource):
    """
    Expected behaviour:
    The input list gets chopped up into chunks of 'members_per_call' length
    This should trigger list_length/members_per_call aiohttp POST requests that return batch operation resources
    We use custom settings so no warning should have been logged
    """

    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with aioresponses() as async_request_mock:
        # as the length of expected_members is 100 and we'll ask for 10 members per call there should be 10 requests
        for i in range(10):
            async_request_mock.post(f'{api_endpoint}/batches', payload=expected_batch_operation_resource)

        response = batch_update_members_async(list_id=expected_members_with_custom_session['list_id'],
                                              member_list=expected_members_with_custom_session['members'],
                                              members_per_call=10, api_endpoint=api_endpoint, api_key=api_key)
        assert len(response) == 10
        for i in range(10):
            assert response[i].__dict__ == expected_batch_operation_resource

        assert f'using default api key setting' not in caplog.text


def test_update_members_async(caplog, expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch2)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][1][1]['data']

        assert loads(request1_data) == batch1
        assert loads(request2_data) == batch2

        # check responses
        assert response[0] == batch1
        assert response[1] == batch2

        assert f'using default api key setting' in caplog.text


def test_update_members_async_with_custom_api_settings(caplog, expected_member_batches):
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{api_endpoint}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{api_endpoint}/lists/{list_id}', payload=batch2)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        api_endpoint=api_endpoint, api_key=api_key)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{api_endpoint}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{api_endpoint}/lists/{list_id}')][1][1]['data']

        assert loads(request1_data) == batch1
        assert loads(request2_data) == batch2

        # check responses
        assert response[0] == batch1
        assert response[1] == batch2

        assert f'using default api key setting' not in caplog.text


def test_update_members_async_status_only(caplog, expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch2)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        status_only=True)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][1][1]['data']

        assert loads(request1_data) == batch1
        assert loads(request2_data) == batch2

        # check responses
        assert response[0] == 200
        assert response[1] == 200

        assert f'using default api key setting' in caplog.text


def test_update_members_async_status_only_failed_response(caplog, expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', status=400)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        status_only=True,
                                        retry=1)

        assert response[0] == 200
        assert response[1] == 400

        assert f'using default api key setting' in caplog.text


def test_update_members_async_failed_response_only_return_status(caplog):

    with aioresponses() as async_request_mock:
        list_id = 'hailthefail'
        member_list = [MemberFactory(list_id=list_id) for _ in range(10)]

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', status=400)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        status_only=False,
                                        retry=1)

        assert response[0] == 400

        assert f'using default api key setting' in caplog.text
