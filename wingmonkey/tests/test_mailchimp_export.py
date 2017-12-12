from requests_mock import Mocker
from pytest import fixture
from json import dumps
from datetime import datetime

from wingmonkey.settings import DEFAULT_MAILCHIMP_EXPORT_ROOT, DEFAULT_MAILCHIMP_ROOT, DEFAULT_MAILCHIMP_API_KEY
from wingmonkey.enums import MemberStatus
from wingmonkey.mailchimp_export import get_all_members
from wingmonkey.enums import MergeFieldTypes


@fixture
def expected_members():
    return b'["Email Address","First Name","Last Name","MEMBER_RATING","OPTIN_TIME","OPTIN_IP","CONFIRM_TIME",' \
           b'"CONFIRM_IP","LATITUDE","LONGITUDE","GMTOFF","DSTOFF","TIMEZONE","CC","REGION","LAST_CHANGED",' \
           b'"LEID","EUID","NOTES"]\n["djones@hotmail.com","David","Boyle",2,"",null,"2017-07-17 00:00:00",null,null,' \
           b'null,null,null,null,null,null,"2017-07-13 14:08:09","15403093","fec418fd22",null]\n ' \
           b'["vanessa64@hotmail.com","Ivan","Knight",2,"",null,"2017-07-17 00:00:00",null,null,null,null,null,null,' \
           b'null,null,"2017-07-17 00:00:00","15403097","b830edc048",null]\n'


@fixture
def expected_merge_field_collection():
    return {
        'merge_fields': [
            {
                'merge_id': 1,
                'tag': 'FNAME',
                'name': 'First Name',
                'type': MergeFieldTypes.TEXT,
                'required': False,
                'default_value': None,
                'public': False,
                'display_order': 1,
                'options': None,
                'help_text': None,
                'list_id': 'jbrrwky1689',
                '_links': None
            },
            {
                'merge_id': 2,
                'tag': 'LNAME',
                'name': 'Last Name',
                'type': MergeFieldTypes.TEXT,
                'required': False,
                'default_value': None,
                'public': False,
                'display_order': 2,
                'options': None,
                'help_text': None,
                'list_id': 'jbrrwky1689',
                '_links': None
            },
        ],
        'list_id': 'jbrrwky1689',
        'total_items': 1,
        '_links': None
    }


def test_get_all_members(expected_members, expected_merge_field_collection):
    list_id = 'jbrrwky1689'
    status = MemberStatus.SUBSCRIBED
    segment = 1
    since = datetime(2017, 7, 17)
    hashed = None
    query_string = (f'apikey={DEFAULT_MAILCHIMP_API_KEY}&id={list_id}&status={status}&segment={segment}&since='
                    f'{datetime.strftime(since, "%Y-%m-%d %H:%M:%S")}')
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field_collection["list_id"]}/merge-fields',
                         text=dumps(expected_merge_field_collection))
        request_mock.get(f'{DEFAULT_MAILCHIMP_EXPORT_ROOT}/list/?{query_string}',
                         content=expected_members, complete_qs=True)
        members = get_all_members(list_id, status, segment, since, hashed)
        assert members[0].email_address == 'djones@hotmail.com'
        assert members[1].email_address == 'vanessa64@hotmail.com'


def test_get_all_members_default_params(expected_members, expected_merge_field_collection):
    list_id = 'jbrrwky1689'
    status = MemberStatus.SUBSCRIBED
    query_string = f'apikey={DEFAULT_MAILCHIMP_API_KEY}&id={list_id}&status={status}'
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field_collection["list_id"]}/merge-fields',
                         text=dumps(expected_merge_field_collection))
        request_mock.get(f'{DEFAULT_MAILCHIMP_EXPORT_ROOT}/list/?{query_string}',
                         content=expected_members, complete_qs=True)
        members = get_all_members(list_id)
        assert members[0].email_address == 'djones@hotmail.com'
        assert members[1].email_address == 'vanessa64@hotmail.com'


def test_get_all_members_hashed(expected_merge_field_collection):
    list_id = 'jbrrwky1689'
    status = MemberStatus.SUBSCRIBED
    segment = 1
    since = datetime(2017, 7, 17)
    hashed = 'sha256'
    query_string = f'apikey={DEFAULT_MAILCHIMP_API_KEY}&id={list_id}&status={status}&segment={segment}&since=' \
                   f'{datetime.strftime(since, "%Y-%m-%d %H:%M:%S")}&hashed={hashed}'
    hashed_members = b'["EMAIL_HASH"]\n["958b4050e18d1d59a58346d67d8831409a770b0bd5ac227ed04d43b2815810e9"]\n' \
                     b'["8ff789bf35df8767fb064a940c4d5aa6115d1d013ea090b5d9fc0b402f23ac9d"]'
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field_collection["list_id"]}/merge-fields',
                         text=dumps(expected_merge_field_collection))
        request_mock.get(f'{DEFAULT_MAILCHIMP_EXPORT_ROOT}/list/?{query_string}',
                         content=hashed_members, complete_qs=True)
        members = get_all_members(list_id, status, segment, since, hashed)
        assert members[0] == '958b4050e18d1d59a58346d67d8831409a770b0bd5ac227ed04d43b2815810e9'
        assert members[1] == '8ff789bf35df8767fb064a940c4d5aa6115d1d013ea090b5d9fc0b402f23ac9d'
