from requests_mock import Mocker
from pytest import fixture
from json import dumps

from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.merge_fields import (MergeField, MergeFieldSerializer, MergeFieldCollection,
                                     MergeFieldCollectionSerializer, get_merge_field_mapping, match_tag_to_name)
from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import MergeFieldTypes


merge_field_serializer = MergeFieldSerializer()
merge_field_collection_serializer = MergeFieldCollectionSerializer()


@fixture
def expected_merge_field():
    return {
        'merge_id': 12345,
        'tag': 'FIRSRTR',
        'name': 'Firestarter',
        'type': MergeFieldTypes.TEXT,
        'required': False,
        'default_value': None,
        'public': False,
        'display_order': 1,
        'options': None,
        'help_text': None,
        'list_id': 'TheFatOfTheLand',
        '_links': None
    }


@fixture
def expected_merge_field_collection(expected_merge_field):
    return {
        'merge_fields': [
            expected_merge_field
        ],
        'list_id': 'TheFatOfTheLand',
        'total_items': 1,
        '_links': None
    }


def compare_result(merge_field, expected=None):

    if expected is None:
        return
    elif not isinstance(expected, dict):
        expected = expected.__dict__

    assert merge_field.merge_id == expected['merge_id']
    assert merge_field.tag == expected['tag']
    assert merge_field.name == expected['name']
    assert merge_field.type == expected['type']
    assert merge_field.required == expected['required']
    assert merge_field.default_value == expected['default_value']
    assert merge_field.public == expected['public']
    assert merge_field.display_order == expected['display_order']
    assert merge_field.options == expected['options']
    assert merge_field.help_text == expected['help_text']
    assert merge_field.list_id == expected['list_id']
    assert merge_field._links == expected['_links']

    return True


def test_merge_field_with_tag_not_str(expected_merge_field):
    merge_field = expected_merge_field.copy()
    merge_field['tag'] = 123
    assert MergeField(**merge_field).tag == '123'


def test_merge_field_create(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields',
                          text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.create(merge_field.list_id, merge_field), expected_merge_field)


def test_merge_field_read(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.get(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/'
            f'{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.read(merge_field.list_id, merge_field.merge_id),
                              expected_merge_field)


def test_merge_field_update(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.patch(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/'
            f'{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.update(merge_field.list_id, merge_field),
                              expected_merge_field)


def test_merge_field_delete(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.delete(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/'
            f'{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert merge_field_serializer.delete(merge_field.list_id, merge_field.merge_id)


def test_merge_field_collection_read(expected_merge_field_collection):

    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_merge_field_collection["list_id"]}/merge-fields',
                         text=dumps(expected_merge_field_collection))
        merge_field_collection = merge_field_collection_serializer.read(expected_merge_field_collection['list_id'])
        expected_merge_fields = MergeFieldCollection(**expected_merge_field_collection)
        assert (merge_field_collection.merge_fields[0]['merge_id'] ==
                expected_merge_fields.merge_fields[0]['merge_id'])
        assert merge_field_collection.total_items == expected_merge_fields.total_items


def test_get_merge_field_mapping(expected_merge_field_collection, expected_merge_field):
    mapped_collection = get_merge_field_mapping(MergeFieldCollection(**expected_merge_field_collection))

    assert mapped_collection == {expected_merge_field['tag']: expected_merge_field['name']}


def test_match_tag_to_name(expected_merge_field):
    assert match_tag_to_name('Firestarter', expected_merge_field) == 'name'


def test_merge_field_serializer():
    session = MailChimpSession()
    serializer = MergeFieldSerializer(session=session)
    assert serializer.session == session


def test_merge_field_collection_serializer():
    session = MailChimpSession()
    serializer = MergeFieldCollectionSerializer(session=session)
    assert serializer.session == session
