from requests_mock import Mocker
from pytest import fixture
from logging import WARNING
from json import dumps

from wingmonkey.lists import List, ListCollection, ListSerializer, ListCollectionSerializer, get_all_lists
from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import VISIBILITY_PRIVATE


list_serializer = ListSerializer()
list_collection_serializer = ListCollectionSerializer()


@fixture
def expected_list():
    return {
            'id': 'FRMN99',
            'web_id': 'VRTGNT99',
            'name': 'Gordon Freeman',
            'contact': {
                'city': 'Unknown',
                'zip': '1234',
                'address1': 'Black Rock',
                'company': 'Black Mesa Research Facility',
                'phone': '', 'state': 'New Mexico',
                'country': 'US', 'address2': ''
             },
            'notify_on_subscribe': '',

            'permission_reminder': 'You get this mail because you are a member of BMRF',
            'campaign_defaults': {
                 'from_name': 'Black Mesa',
                 'subject': '',
                 'language': 'en',
                 'from_email': 'gman@bmrf.gov'
                 },
            'modules': None,
            'subscribe_url_long': None,
            'email_type_option': False,
            'notify_on_unsubscribe': '',
            'stats': None,
            'subscribe_url_short': None,
            'visibility': VISIBILITY_PRIVATE,
            'date_created': None,
            'list_rating': None,

            'use_archive_bar': False,
            'beamer_address': None,
            '_links': None,
           }


@fixture
def expected_lists():
    return {
            'lists': [
                {
                    'id': 'FRMN99',
                    'web_id': 'VRTGNT99',
                    'name': 'Gordon Freeman',
                    'notify_on_subscribe': '',
                    'email_type_option': False,
                    'permission_reminder': 'You get this mail because you are a member of BMRF',
                    'campaign_defaults': {
                                          'from_name': 'Black Mesa',
                                          'subject': '',
                                          'language': 'en',
                                          'from_email': 'gman@bmrf.gov'
                                          },
                    'notify_on_unsubscribe': '',
                    'contact': {
                                'city': 'Unknown',
                                'zip': '1234',
                                'address1': 'Black Rock',
                                'company': 'Black Mesa Research Facility',
                                'phone': '', 'state': 'New Mexico',
                                'country': 'US',
                                'address2': ''
                               },
                    'visibility': VISIBILITY_PRIVATE,
                    'use_archive_bar': False}],
            'total_items': 1,
            }


def compare_result(mailchimp_list, expected=None):
    """

    :param mailchimp_list: List instance
    :param expected: List Instance or str
    :return: boolean
    """
    if expected is None:
        return
    elif not isinstance(expected, dict):
        expected = expected.__dict__

    assert mailchimp_list.id == expected['id']
    assert mailchimp_list.web_id == expected['web_id']
    assert mailchimp_list.name == expected['name']
    assert mailchimp_list.contact == expected['contact']
    assert mailchimp_list.permission_reminder == expected['permission_reminder']
    assert mailchimp_list.use_archive_bar == expected['use_archive_bar']
    assert mailchimp_list.campaign_defaults == expected['campaign_defaults']
    assert mailchimp_list.notify_on_subscribe == expected['notify_on_subscribe']
    assert mailchimp_list.notify_on_unsubscribe == expected['notify_on_unsubscribe']
    assert mailchimp_list.date_created == expected['date_created']
    assert mailchimp_list.list_rating == expected['list_rating']
    assert mailchimp_list.email_type_option == expected['email_type_option']
    assert mailchimp_list.subscribe_url_short == expected['subscribe_url_short']
    assert mailchimp_list.subscribe_url_long == expected['subscribe_url_long']
    assert mailchimp_list.beamer_address == expected['beamer_address']
    assert mailchimp_list.visibility == expected['visibility']
    assert mailchimp_list.modules == expected['modules']
    assert mailchimp_list.stats == expected['stats']
    assert mailchimp_list._links == expected['_links']

    return True


def test_list_create(expected_list):
    mailchimp_list = List(**expected_list)
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists', text=dumps(expected_list))
        assert compare_result(list_serializer.create(mailchimp_list), expected_list)


def test_list_read(expected_list):
    mailchimp_list = List(**expected_list)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_list["id"]}', text=dumps(expected_list))
        assert compare_result(list_serializer.read(mailchimp_list.id), expected_list)


def test_list_read_no_id(expected_list, expected_lists):
    mailchimp_list = List(**expected_list)
    mailchimp_list.id = None
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists', text=dumps(expected_lists))
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_list["id"]}', text=dumps(expected_list))
        assert compare_result(list_serializer.read(), expected_list)


def test_list_read_no_id_no_lists(caplog):
    empty_list_collection = dict(lists=[])
    caplog.set_level(WARNING)
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists', text=dumps(empty_list_collection))
        list_serializer.read()
        assert 'No lists found on server' in caplog.text


def test_list_update(expected_list):
    mailchimp_list = List(**expected_list)
    with Mocker() as request_mock:
        request_mock.patch(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_list["id"]}', text=dumps(expected_list))
        assert compare_result(list_serializer.update(mailchimp_list), expected_list)


def test_list_delete(expected_list):
    mailchimp_list = List(**expected_list)
    with Mocker() as request_mock:
        request_mock.delete(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_list["id"]}', text='')
        assert list_serializer.delete(mailchimp_list)


def test_lists_read(expected_lists):

    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists', text=dumps(expected_lists))
        mailchimp_lists = list_collection_serializer.read()
        expected_lists = ListCollection(**expected_lists)
        assert mailchimp_lists.lists == expected_lists.lists
        assert mailchimp_lists.total_items == expected_lists.total_items


def test_get_all_lists(expected_lists):
    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists', text=dumps(expected_lists))
        mailchimp_lists = get_all_lists()
        expected_lists = ListCollection(**expected_lists)
        assert mailchimp_lists.lists == expected_lists.lists


def test_get_all_lists_custom_session(expected_lists):
    api_endpoint = 'https://tst1.api.mailchimp.com/3.0'
    api_key = '1234-tst1'
    session = MailChimpSession(api_endpoint=api_endpoint, api_key=api_key)

    with Mocker() as request_mock:
        request_mock.get(f'{api_endpoint}/lists', text=dumps(expected_lists))
        mailchimp_lists = get_all_lists(session=session)
        expected_lists = ListCollection(**expected_lists)
        assert mailchimp_lists.lists == expected_lists.lists


def test_list_collection_serializer():
    session = MailChimpSession()
    list_collection_serializer = ListCollectionSerializer(session=session)
    assert list_collection_serializer.session == session
