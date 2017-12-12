from requests_mock import Mocker
from datetime import datetime
from pytest import fixture
from json import dumps

from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import MemberStatus
from wingmonkey.batch_operations import batch_add_members, batch_update_members, batch_delete_members, \
    BatchOperationResourceSerializer, BatchOperationResource, BatchOperationResourceCollectionSerializer, \
    BatchOperationResourceCollection
from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.members import Member


@fixture()
def expected_batch_operation_resource():
    return {
        'id': 'wereallresources123',
        'status': 'pending',
        'total_operations': 1,
        'finished_operations': 0,
        'errored_operations': 0,
        'submitted_at': datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S'),
        'completed_at': None,
        'response_body_url': 'https://amailchimp/link/goes/here',
        '_links': None,
    }


@fixture()
def expected_member():
    return {
        '_links': None,
        'email_address': 'adoringfan@stalkmail.com',
        'email_client': 'Lookout On Purpose',
        'email_type': 'html',
        'id': 'KRBL101',
        'interests': None,
        'ip_opt': '1.1.1.1',
        'ip_signup': '',
        'language': '',
        'last_changed': None,
        'last_note': None,
        'list_id': 'ListyMcListface',
        'location': {
            'country_code': '',
            'dstoff': 0,
            'gmtoff': 0,
            'latitude': 0,
            'longitude': 0,
            'timezone': ''
        },
        'member_rating': 2,
        'merge_fields': {'FNAME': 'Eddie', 'LNAME': 'Emmer'},
        'stats': {'avg_click_rate': 0, 'avg_open_rate': 0},
        'status': MemberStatus.SUBSCRIBED,
        'timestamp_opt': None,
        'unique_email_id': None,
        'unsubscribe_reason': None,
        'vip': False
        }


def test_batch_add_members(expected_batch_operation_resource, expected_member):

    def match_request_text(request):
        return 'lists/alistid1234/members' in (request.text or '')

    members = [Member(**expected_member)]
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/batches',
                          text=dumps(expected_batch_operation_resource), additional_matcher=match_request_text)
        result = batch_add_members('alistid1234', members)
        assert result.id == expected_batch_operation_resource['id']


def test_batch_update_members(expected_batch_operation_resource, expected_member):

    expected_member2 = expected_member
    expected_member2['id'] = 'KRBL202'

    def match_request_text(request):
        return f'lists/alistid1234/members/{expected_member["id"]}' and \
               f'lists/alistid1234/members/{expected_member2["id"]}' in (request.text or '')

    members = [Member(**expected_member), Member(**expected_member2)]
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/batches',
                          text=dumps(expected_batch_operation_resource), additional_matcher=match_request_text)
        result = batch_update_members('alistid1234', members)
        assert result.id == expected_batch_operation_resource['id']


def test_batch_delete_members(expected_batch_operation_resource, expected_member):

    def match_request_text(request):
        return 'lists/alistid1234/members' in (request.text or '')

    members = [Member(**expected_member)]
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/batches',
                          text=dumps(expected_batch_operation_resource), additional_matcher=match_request_text)
        assert batch_delete_members('alistid1234', members)


def test_batch_operation_resource_serializer():
    serializer = BatchOperationResourceSerializer()
    assert isinstance(serializer.session, MailChimpSession)


def _compare_batch_operation_resource_result(batch, expected=None):
    if expected is None:
        return False
    elif not isinstance(expected, dict):
        expected = expected.__dict__

    assert batch.id == expected['id']
    assert batch.status == expected['status']
    assert batch.total_operations == expected['total_operations']
    assert batch.finished_operations == expected['finished_operations']
    assert batch.errored_operations == expected['errored_operations']
    assert batch.submitted_at == datetime.strptime(expected['submitted_at'], '%Y-%m-%d %H:%M:%S')
    assert batch.completed_at == expected['completed_at']
    assert batch.response_body_url == expected['response_body_url']
    assert batch._links == expected['_links']

    return True


def test_batch_operation_resource_serializer_read(expected_batch_operation_resource):
    serializer = BatchOperationResourceSerializer()
    batch = BatchOperationResource(**expected_batch_operation_resource)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/batches/{expected_batch_operation_resource["id"]}',
                         text=dumps(expected_batch_operation_resource))
        assert _compare_batch_operation_resource_result(serializer.read(batch_id=batch.id),
                                                        expected_batch_operation_resource)


def test_batch_operation_resource_serializer_delete(expected_batch_operation_resource):
    serializer = BatchOperationResourceSerializer()
    batch = BatchOperationResource(**expected_batch_operation_resource)
    with Mocker() as request_mock:
        request_mock.delete(f'{DEFAULT_MAILCHIMP_ROOT}/batches/{expected_batch_operation_resource["id"]}', text='')
        assert serializer.delete(batch.id)


@fixture
def expected_batch_operation_resource_collection(expected_batch_operation_resource):
    return {
        'batches': [
            expected_batch_operation_resource
        ],
        'total_items': 1,
        '_links': None
    }


def test_batch_operation_resource_collection_serializer():
    serializer = BatchOperationResourceCollectionSerializer()
    assert isinstance(serializer.session, MailChimpSession)


def test_batch_operation_resource_collection(expected_batch_operation_resource_collection):
    expected = expected_batch_operation_resource_collection
    collection = BatchOperationResourceCollection(**expected_batch_operation_resource_collection)
    assert collection.total_items == expected['total_items']
    assert collection._links == expected['_links']
    assert collection.batches[0]['id'] == expected['batches'][0]['id']
