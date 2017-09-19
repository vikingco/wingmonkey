from copy import deepcopy
from datetime import datetime
from requests_mock import Mocker
from json import dumps
from pytest import fixture
from aioresponses import aioresponses

from wingmonkey.settings import MAILCHIMP_ROOT
from wingmonkey.factories import MemberFactory
from wingmonkey.members import MemberSerializer
from wingmonkey.async_operations import get_all_members_async, batch_update_members_async


@fixture()
def expected_members():
    return {
        'members': [MemberSerializer().dumps(MemberFactory(list_id='ListyMcListface')).data for _ in range(100)],
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
        request_mock.get(f'{MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                         text=dumps({'total_items': 100}))
        # We will use max_count=10 which means 10 (100/10) async get tasks should be executed in this case
        chunks = _create_chunks(expected_members, chunk_size=10)
        for i in range(10):
            async_request_mock.get(f'{MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                                   body=dumps(chunks[i]))

        response = get_all_members_async(list_id=expected_members["list_id"], max_count=10)
        assert response.members == expected_members['members']


def test_batch_update_members_async(expected_members, expected_batch_operation_resource):
    """
    Expected behaviour:
    The input list gets chopped up into chunks of 'members_per_call' length
    This should trigger list_length/members_per_call aiohttp POST requests that return batch operation resources
    """
    with aioresponses() as async_request_mock:
        # as the length of expected_members is 100 and we'll ask for 10 members per call there should be 10 requests
        for i in range(10):
            async_request_mock.post(f'{MAILCHIMP_ROOT}/batches', payload=expected_batch_operation_resource)

        response = batch_update_members_async(list_id=expected_members['list_id'],
                                              member_list=expected_members['members'], members_per_call=10)
        assert len(response) == 10
        for i in range(10):
            assert response[i].__dict__ == expected_batch_operation_resource
