from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.async_operations import get_all_members_async
from wingmonkey.batch_operations import (BatchOperation, BatchOperationCollection, BatchOperationResource,
                                         BatchOperationSerializer, BatchOperationResourceSerializer)
from wingmonkey.enums import MemberStatus
from wingmonkey.members import Member, MemberBatchRequestSerializer, MemberBatchRequest


def unsubscribe_members(list_id, member_list=None, session=None):
    """
    Unsubscribe all members of given list
    :param list_id: Str: id of list to unsubscribe members from
    :param member_list: List: Optional list of members to unsubscribe instead of defaulting to all members of list
    :param session: MailChimpSession
    :return: BatchOperationResource
    """

    if not session:
        session = MailChimpSession()

    if not member_list:
        all_subscribed_members = get_all_members_async(list_id, max_count=1000, max_chunks=9,
                                                       extra_params=dict(status='subscribed'),
                                                       api_endpoint=session.api_endpoint, api_key=session.api_key)
        if not all_subscribed_members:
            return
        member_list = all_subscribed_members

    members_to_update = []

    for member in member_list.members:
        member['status'] = MemberStatus.UNSUBSCRIBED
        members_to_update.append(Member(**member))

    return member_batch_update(list_id=list_id, member_list=members_to_update, session=session)


def member_batch_update(list_id, member_list, session=None):
    """
    Creates batch operations of batch member requests
    :param list_id: Str: id of list to create/update members in
    :param member_list: List: list of Member instances
    :param session: MailChimpSession
    :return: BatchOperationResource instance
    """

    if not session:
        session = MailChimpSession()

    batches = []
    operations = []
    member_batch_request_serializer = MemberBatchRequestSerializer(session=session)
    # split huge lists into multiple batches to prevent time outs
    for chunk in generate_chunks(member_list, 500):
        batch_request = MemberBatchRequest(members=chunk, update_existing=True)
        batches.append(member_batch_request_serializer.create(list_id=list_id,
                                                              member_batch_request_instance=batch_request))
    path = f'lists/{list_id}/members'
    for batch in batches:
        operations.append(BatchOperation(method='POST', path=path,
                                         body=member_batch_request_serializer.dumps(batch).data))

    batch_operation_serializer = BatchOperationSerializer(session=session)
    batch_operation_resource_serializer = BatchOperationResourceSerializer(session=session)

    batch_operations = BatchOperationCollection(operations=operations)
    response = session.post('batches', json=batch_operation_serializer.dumps(batch_operations).data)

    batch_operation_resource = BatchOperationResource(**batch_operation_resource_serializer.load(response.json()).data)

    return batch_operation_resource


def generate_chunks(input_list, chunk_size):
    """Generator that returns chunk_size slices of given list"""
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]
