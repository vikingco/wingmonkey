from requests_mock import Mocker
from pytest import fixture
from json import dumps
from datetime import datetime

from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.segments import Segment, SegmentSerializer, SegmentCollection, SegmentCollectionSerializer
from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import SegmentFieldTypes


segment_serializer = SegmentSerializer()
segment_collection_serializer = SegmentCollectionSerializer()


@fixture
def expected_segment():
    return {
        'id': 1234,
        'name': 'Coffee Addicts',
        'member_count': 99,
        'type': SegmentFieldTypes.SAVED,
        'created_at': datetime.strftime(datetime(2017, 7, 7), '%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.strftime(datetime(2017, 7, 17), '%Y-%m-%d %H:%M:%S'),
        'options': dict(
            conditions=[dict(condition_type='TextMerge', field='COFVEVE', op='blank_not')],
            match='all'
        ),
        'list_id': 'OCD123',
        '_links': None
    }


@fixture
def expected_segments_collection(expected_segment):
    return {
        'segments': [
            expected_segment
        ],
        'list_id': 'OCD123',
        'total_items': 1,
        '_links': None
    }


def compare_result(segment, expected=None):

    if expected is None:
        return
    elif not isinstance(expected, dict):
        expected = expected.__dict__

    assert segment.id == expected['id']
    assert segment.name == expected['name']
    assert segment.member_count == expected['member_count']
    assert segment.type == expected['type']
    assert segment.created_at == datetime.strptime(expected['created_at'], '%Y-%m-%d %H:%M:%S')
    assert segment.updated_at == datetime.strptime(expected['updated_at'], '%Y-%m-%d %H:%M:%S')
    assert segment.options == expected['options']
    assert segment.list_id == expected['list_id']
    assert segment._links == expected['_links']

    return True


def test_segment_create(expected_segment):
    segment = Segment(**expected_segment)
    with Mocker() as request_mock:
        request_mock.post(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_segment["list_id"]}/segments',
                          text=dumps(expected_segment))
        assert compare_result(segment_serializer.create(segment.list_id, segment), expected_segment)


def test_segment_read(expected_segment):
    segment = Segment(**expected_segment)
    with Mocker() as request_mock:
        request_mock.get(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_segment["list_id"]}/segments/{expected_segment["id"]}',
            text=dumps(expected_segment))
        assert compare_result(segment_serializer.read(segment.list_id, segment.id), expected_segment)


def test_segment_update(expected_segment):
    segment = Segment(**expected_segment)
    with Mocker() as request_mock:
        request_mock.patch(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_segment["list_id"]}/segments/{expected_segment["id"]}',
            text=dumps(expected_segment))
        assert compare_result(segment_serializer.update(segment.list_id, segment), expected_segment)


def test_segment_delete(expected_segment):
    segment = Segment(**expected_segment)
    with Mocker() as request_mock:
        request_mock.delete(
            f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_segment["list_id"]}/segments/{expected_segment["id"]}',
            text='')
        assert segment_serializer.delete(segment.list_id, segment.id)


def test_segments_collection_read(expected_segments_collection):

    with Mocker() as request_mock:
        request_mock.get(f'{DEFAULT_MAILCHIMP_ROOT}/lists/{expected_segments_collection["list_id"]}/segments',
                         text=dumps(expected_segments_collection))
        segments_collection = segment_collection_serializer.read(expected_segments_collection['list_id'])
        expected_segments = SegmentCollection(**expected_segments_collection)
        assert segments_collection.segments[0]['id'] == expected_segments.segments[0]['id']
        assert segments_collection.total_items == expected_segments.total_items


def test_segment_serializer():
    session = MailChimpSession()
    serializer = SegmentSerializer(session=session)
    assert serializer.session, session


def test_segment_collection_serializer():
    session = MailChimpSession()
    serializer = SegmentCollectionSerializer(session=session)
    assert serializer.session == session
