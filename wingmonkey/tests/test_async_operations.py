from copy import deepcopy
from types import GeneratorType
from datetime import datetime
from requests_mock import Mocker
from json import dumps, loads
from pytest import fixture
from aioresponses import aioresponses
from asyncio import TimeoutError
from unittest.mock import patch
from asynctest.mock import patch as async_patch
from logging import INFO

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


def test_get_all_members_async(expected_members):
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
        for member in expected_members['members']:
            assert member in response.members


def test_get_all_members_async_exception(expected_members):
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


def test_get_all_members_async_timeout_exception(caplog, expected_members):
    caplog.set_level(INFO)
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with patch('wingmonkey.async_operations._get_all_members_async', side_effect=TimeoutError):
        with Mocker() as request_mock:
            request_mock.get(f'{api_endpoint}/lists/{expected_members["list_id"]}/members', status_code=400)

            assert not get_all_members_async(list_id=expected_members["list_id"], max_count=10, retry=1,
                                             sleepy_time=0, api_endpoint=api_endpoint, api_key=api_key)

            assert f'get_all_members_async for list {expected_members["list_id"]} failed. Error' in caplog.text


def test_get_all_members_async_exception_in_response(caplog, expected_members):
    caplog.set_level(INFO)
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with Mocker() as request_mock:
        with async_patch('wingmonkey.async_operations._get_response', side_effect=Exception):
            request_mock.get(f'{api_endpoint}/lists/{expected_members["list_id"]}/members',
                             text=dumps({'total_items': 100}))

            get_all_members_async(list_id=expected_members["list_id"], max_count=10, retry=1,
                                  sleepy_time=0, api_endpoint=api_endpoint, api_key=api_key)
            assert f'wingmonkey.get_all_members_async chunk raised exception' in caplog.text


def test_batch_update_members_async(expected_members, expected_batch_operation_resource):
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


def test_get_all_members_async_with_custom_api_settings(expected_members_with_custom_session):
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

        for member in expected_members_with_custom_session['members']:
            assert member in response.members


def test_batch_update_members_async_with_custom_api_settings(expected_members_with_custom_session,
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


def test_update_members_async(expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch2)

        responses = update_members_async(list_id=list_id,
                                         member_list=member_list)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][1][1]['data']

        request_data = [loads(request1_data), loads(request2_data)]

        assert batch1 in request_data
        assert batch2 in request_data

        # check responses
        assert batch1 in responses
        assert batch2 in responses


def test_update_members_async_with_custom_api_settings(expected_member_batches):
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{api_endpoint}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{api_endpoint}/lists/{list_id}', payload=batch2)

        responses = update_members_async(list_id=list_id,
                                         member_list=member_list,
                                         api_endpoint=api_endpoint, api_key=api_key)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{api_endpoint}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{api_endpoint}/lists/{list_id}')][1][1]['data']

        request_data = [loads(request1_data), loads(request2_data)]

        assert batch1 in request_data
        assert batch2 in request_data

        # check responses
        assert batch1 in responses
        assert batch2 in responses


def test_update_members_async_status_only(expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch2)

        responses = update_members_async(list_id=list_id,
                                         member_list=member_list,
                                         status_only=True)

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][1][1]['data']

        request_data = [loads(request1_data), loads(request2_data)]

        assert batch1 in request_data
        assert batch2 in request_data

        # check responses
        assert 200 in responses
        assert 200 in responses


def test_update_members_async_status_only_failed_response(expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', status=400)

        responses = update_members_async(list_id=list_id,
                                         member_list=member_list,
                                         status_only=True,
                                         retry=1)

        assert 200 in responses
        assert 400 in responses


def test_update_members_async_failed_response():

    with aioresponses() as async_request_mock:
        list_id = 'hailthefail'
        member_list = [MemberFactory(list_id=list_id) for _ in range(10)]

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', status=400)

        response = update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        status_only=False,
                                        retry=1)

        assert response == []


def test_update_members_async_callback(expected_member_batches):

    with aioresponses() as async_request_mock:
        # as the length of expected_members_thousand is 1000 and max members per POST is 500 we expect 2 requests
        batch1, batch2, member_list = expected_member_batches
        list_id = member_list[0].list_id
        callback_status = []

        def callback():
            while True:
                progress = yield
                callback_status.append(dict(total=progress.total, completed=progress.completed,
                                            status=progress.last_response_status))

        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch1)
        async_request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}', payload=batch2)

        responses = update_members_async(list_id=list_id,
                                         member_list=member_list,
                                         callback=callback())

        # check if correct requests have been made
        request1_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][0][1]['data']
        request2_data = async_request_mock.requests[(f'POST',
                                                     f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}')][1][1]['data']

        request_data = [loads(request1_data), loads(request2_data)]
        assert batch1 in request_data
        assert batch2 in request_data

        # check responses
        assert batch1 in responses
        assert batch2 in responses

        assert callback_status == [
            {'total': 1000, 'completed': 0, 'status': None},
            {'total': 1000, 'completed': 500, 'status': 200},
            {'total': 1000, 'completed': 1000, 'status': 200},
        ]


def test_update_members_async_callback_wrong_type(caplog):

    def non_generator_callback():
        return 'call on meeeeee'

    with aioresponses():
        list_id = 'hailthefail'
        member_list = [MemberFactory(list_id=list_id) for _ in range(10)]

        assert not update_members_async(list_id=list_id,
                                        member_list=member_list,
                                        callback=non_generator_callback())

        assert f'callback should be {GeneratorType} but got {type(non_generator_callback())} instead' in caplog.text
