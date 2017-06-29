from requests_mock import Mocker
from pytest import fixture
from json import dumps

from wingmonkey.members import Member, MemberSerializer
from wingmonkey.lists import ListSerializer
from wingmonkey.settings import MAILCHIMP_ROOT
from wingmonkey.enums import MemberStatus

list_serializer = ListSerializer()
member_serializer = MemberSerializer()


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


@fixture()
def expected_members(expected_member):
    return {
        'members': [
            expected_member
        ],
        'list_id': 'ListyMcListface',
        'total_items': 1,
        '_links': None
    }


def compare_result(member, expected=None):
    """

    :param member: List instance
    :param expected: List Instance or str
    :return: boolean
    """
    if expected is None:
        return
    elif not isinstance(expected, dict):
        expected = expected.__dict__

    assert member.id == expected['id']
    assert member.email_address == expected['email_address']
    assert member.unique_email_id == expected['unique_email_id']
    assert member.email_type == expected['email_type']
    assert member.status == expected['status']
    assert member.unsubscribe_reason == expected['unsubscribe_reason']
    assert member.merge_fields == expected['merge_fields']
    assert member.interests == expected['interests']
    assert member.stats == expected['stats']
    assert member.ip_signup == expected['ip_signup']
    assert member.ip_opt == expected['ip_opt']
    assert member.timestamp_opt == expected['timestamp_opt']
    assert member.member_rating == expected['member_rating']
    assert member.last_changed == expected['last_changed']
    assert member.language == expected['language']
    assert member.vip == expected['vip']
    assert member.email_client == expected['email_client']
    assert member.location == expected['location']
    assert member.last_note == expected['last_note']
    assert member.list_id == expected['list_id']
    assert member._links == expected['_links']

    return True


def test_member_read(expected_member):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.get('{}/lists/{}/members/{}'.format(MAILCHIMP_ROOT, expected_member['list_id'], 
                                                         expected_member['id']), text=dumps(expected_member))
        assert compare_result(member_serializer.read(member.list_id, member.id), expected_member)


def test_member_read_no_id(expected_member, expected_members):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.get('{}/lists/{}/members'.format(MAILCHIMP_ROOT, expected_members['list_id']),
                         text=dumps(expected_members))
        request_mock.get('{}/lists/{}/members/{}'.format(MAILCHIMP_ROOT, expected_member['list_id'],
                                                         expected_member['id']), text=dumps(expected_member))
        assert compare_result(member_serializer.read(member.list_id, member.id), expected_member)
