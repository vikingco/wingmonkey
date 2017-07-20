from requests_mock import Mocker
from pytest import fixture
from json import dumps

from wingmonkey.merge_fields import (MergeField, MergeFieldSerializer, MergeFieldCollection,
                                     MergeFieldCollectionSerializer)
from wingmonkey.settings import MAILCHIMP_ROOT
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


def test_merge_field_create(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.post(f'{MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields',
                          text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.create(merge_field.list_id, merge_field), expected_merge_field)


def test_merge_field_read(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.get(
            f'{MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.read(merge_field.list_id, merge_field.merge_id),
                              expected_merge_field)


def test_merge_field_update(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.patch(
            f'{MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert compare_result(merge_field_serializer.update(merge_field.list_id, merge_field),
                              expected_merge_field)


def test_merge_field_delete(expected_merge_field):
    merge_field = MergeField(**expected_merge_field)
    with Mocker() as request_mock:
        request_mock.delete(
            f'{MAILCHIMP_ROOT}/lists/{expected_merge_field["list_id"]}/merge-fields/{expected_merge_field["merge_id"]}',
            text=dumps(expected_merge_field))
        assert merge_field_serializer.delete(merge_field.list_id, merge_field.merge_id)


def test_merge_field_collection_read(expected_merge_field_collection):

    with Mocker() as request_mock:
        request_mock.get(f'{MAILCHIMP_ROOT}/lists/{expected_merge_field_collection["list_id"]}/merge-fields',
                         text=dumps(expected_merge_field_collection))
        merge_field_collection = merge_field_collection_serializer.read(expected_merge_field_collection['list_id'])
        expected_merge_fields = MergeFieldCollection(**expected_merge_field_collection)
        assert (merge_field_collection.merge_fields[0]['merge_id'] ==
                expected_merge_fields.merge_fields[0]['merge_id'])
        assert merge_field_collection.total_items == expected_merge_fields.total_items
