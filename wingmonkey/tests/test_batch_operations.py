from requests_mock import Mocker
from datetime import datetime
from pytest import fixture
from json import dumps

from wingmonkey.settings import MAILCHIMP_ROOT
from wingmonkey.enums import MemberStatus
from wingmonkey.batch_operations import batch_add_members, batch_update_members, batch_delete_members
from wingmonkey.members import Member


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
        request_mock.post(f'{MAILCHIMP_ROOT}/batches',
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
        request_mock.post(f'{MAILCHIMP_ROOT}/batches',
                          text=dumps(expected_batch_operation_resource), additional_matcher=match_request_text)
        result = batch_update_members('alistid1234', members)
        assert result.id == expected_batch_operation_resource['id']


def test_batch_delete_members(expected_batch_operation_resource, expected_member):

    def match_request_text(request):
        return 'lists/alistid1234/members' in (request.text or '')

    members = [Member(**expected_member)]
    with Mocker() as request_mock:
        request_mock.post(f'{MAILCHIMP_ROOT}/batches',
                          text=dumps(expected_batch_operation_resource), additional_matcher=match_request_text)
        assert batch_delete_members('alistid1234', members)
