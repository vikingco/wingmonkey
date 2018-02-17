from requests_mock import Mocker
from pytest import fixture, raises
from json import dumps
from logging import WARNING

from wingmonkey.mailchimp_session import ClientException, MailChimpSession
from wingmonkey.members import (Member, MemberSerializer, MemberCollection, MemberCollectionSerializer,
                                MemberBatchRequestSerializer, MemberBatchRequest, generate_member_id,
                                MemberActivitySerializer)
from wingmonkey.lists import ListSerializer
from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import MemberStatus

list_serializer = ListSerializer()
member_serializer = MemberSerializer()
members_serializer = MemberCollectionSerializer()


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
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}/members/{expected_member["id"]}',
                         text=dumps(expected_member))
        assert compare_result(member_serializer.read(member.list_id, member.id), expected_member)


def test_member_read_no_id(expected_member, expected_members):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                         text=dumps(expected_members))
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}/members/{expected_member["id"]}',
                         text=dumps(expected_member))
        assert compare_result(member_serializer.read(member.list_id), expected_member)


def test_member_read_no_id_empty_list(caplog, expected_members):
    expected_members.update(members=[])
    caplog.set_level(WARNING)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                         text=dumps(expected_members))
        member_serializer.read(expected_members['list_id'])
        assert 'No members found for list' in caplog.text


def test_member_create(expected_member):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}/members',
                          text=dumps(expected_member))
        assert compare_result(member_serializer.create(member.list_id, member), expected_member)


def test_member_update(expected_member):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.patch(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}/members/{expected_member["id"]}',
            text=dumps(expected_member))
        assert compare_result(member_serializer.update(member.list_id, member), expected_member)


def test_member_delete(expected_member):
    member = Member(**expected_member)
    with Mocker() as request_mock:
        request_mock.delete(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}/members/{expected_member["id"]}',
            text='')
        assert member_serializer.delete(member.list_id, member.id)


def test_members_read(expected_members):
    members = MemberCollection(**expected_members)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_members["list_id"]}/members',
                         text=dumps(expected_members))
        assert members_serializer.read(members.list_id).members[0]['id'] == expected_members['members'][0]['id']


def test_member_batch_request(expected_member):
    expected_member2 = expected_member
    expected_member2['id'] = 'NR2'
    expected_member2['email_address'] = 'another1@bitesthe.dust'
    member_list = [Member(**expected_member), Member(**expected_member2)]
    member_batch_request = MemberBatchRequest(members=member_list)
    expected_batch_response = {
        'new_members': [
            expected_member,
            expected_member2
        ],
        'updated_members': None,
        'errors': None,
        'total_created': 2,
        'total_updated': 0,
        'error_count': 0,
        '_links': None
    }
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_member["list_id"]}',
                          text=dumps(expected_batch_response))
        response = MemberBatchRequestSerializer().create(list_id=expected_member['list_id'],
                                                         member_batch_request_instance=member_batch_request)
        assert response.new_members[0]['email_address'] == expected_batch_response['new_members'][0]['email_address']
        assert response.new_members[1]['email_address'] == expected_batch_response['new_members'][1]['email_address']
        assert response.total_created == expected_batch_response['total_created']


def test_member_batch_request_memberlist_too_big():
    oversized_list = [Member() for _ in range(0, 501)]
    assert raises(ClientException, MemberBatchRequest, members=oversized_list)


def test_member_serializer_without_session():
    session = MailChimpSession()
    serializer = MemberSerializer(session=session)
    assert serializer.session == session


def test_generate_member_id_without_email_address():
    assert not generate_member_id('')


def test_generate_member_id():
    """ Check if the md5 hash of some@email.com """
    expected_hexdigest = 'd8ffeba65ee5baf57e4901690edc8e1b'
    assert generate_member_id(email_address='some@email.com') == expected_hexdigest


def test_member_empty_mergefields():
    member = Member(merge_fields=None)
    assert member.merge_fields == {}


def test_member_mergefield_with_none_value():
    member = Member(merge_fields={'NOTHING': None})
    assert member.merge_fields['NOTHING'] == ''


def test_member_activity_read():
    email_address = 'adoringfan@stalkmail.com'
    list_id = 'no-idea-123'
    expected_member_hash = 'c7e281082239e249d17360a9fffba276'
    expected_member_activity = {
         '_links': None,
         'activity': [{'action': 'subscribe',
                       'campaign_id': '',
                       'timestamp': '2018-02-16T18:23:10+00:00',
                       'type': 'A'}
                      ],
         'email_id': expected_member_hash,
         'list_id': list_id,
         'total_items': 1
    }

    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{list_id}/members/{expected_member_hash}/activity',
                         text=dumps(expected_member_activity))
        response = MemberActivitySerializer().read(list_id='no-idea-123', email_address=email_address)

        assert response.activity == expected_member_activity['activity']
        assert response.email_id == expected_member_hash
