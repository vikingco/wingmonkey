from wingmonkey.members import get_all_members_async
from wingmonkey.batch_operations import batch_update_members
from wingmonkey.enums import MemberStatus
from wingmonkey.members import Member


def unsubscribe_all_members(list_id):

    subscribed_members = get_all_members_async(list_id, max_count=1000, max_chunks=9,
                                               extra_params=dict(status='subscribed'))
    members_to_update = []

    for chunk in subscribed_members:
        for member in chunk['members']:
            member['status'] = MemberStatus.UNSUBSCRIBED
            members_to_update.append(Member(**member))

    batches = []
    # split huge lists into multiple batches to prevent time outs
    for chunk in generate_chunks(members_to_update, 25000):
        batches.append(batch_update_members(list_id=list_id, members_list=chunk))

    return batches


def generate_chunks(input_list, chunk_size):
    """Generator that returns chunk_size slices of given list"""
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]