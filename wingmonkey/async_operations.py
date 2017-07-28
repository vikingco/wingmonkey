from asyncio import get_event_loop, gather, Queue, sleep as async_sleep
from math import ceil
from time import sleep
from uuid import uuid4

from logging import getLogger

from wingmonkey.mailchimp_session import MailChimpSession, ClientException
from wingmonkey.members import (MemberBatchRequest, MemberBatchRequestSerializer, MemberCollection,
                                MemberCollectionSerializer)
from wingmonkey.batch_operations import (BatchOperationResource, BatchOperationResourceSerializer, BatchOperation,
                                         BatchOperationSerializer, BatchOperationCollection)

logger = getLogger(__name__)

async def _async_task(func=None, args=None, kwargs=None, retry=3, sleepy_time=5):
    """

    :param func: Function to be called
    :param args: list , positional args for func
    :param kwargs: dict, keyword args for func
    :param retry: int : amount of retries after exception
    :param sleepy_time: int : waiting time between retries
    :return: return value of func
    """

    if not func:
        # I had func once. It was awful.
        raise TypeError

    task_id = uuid4()

    if not args:
        args = []
    if not kwargs:
        kwargs = {}

    while retry > 0:
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.warning('task %s failed. Error: %s , %i retries left', task_id, e, retry)
            retry -= 1
            await async_sleep(sleepy_time)


async def _get_chunk(queue, results):
    """

    :param queue: asyncio.Queue
    :param results: list
    """
    while not queue.empty():
        task = await queue.get()
        results.append(await _async_task(**task))


async def _batch_update_members_async(queue, list_id, member_list, max_chunks, retry=5):

    tasks = []
    results = []

    with MailChimpSession() as session:

        for i in range(0, len(member_list), 25000):
            partial_list = member_list[i:i + 25000]

            batches = []
            operations = []
            # split lists into batches of 500 (= max allowed members per batch request)
            for j in range(0, len(partial_list), 500):
                batch_request = MemberBatchRequest(members=partial_list[j:j + 500], update_existing=True)
                batches.append(MemberBatchRequestSerializer().create(list_id=list_id,
                                                                     member_batch_request_instance=batch_request))
            path = f'lists/{list_id}/members'
            for batch in batches:
                operations.append(BatchOperation(method='POST', path=path,
                                                 body=MemberBatchRequestSerializer().dumps(batch).data))

            batch_operation_serializer = BatchOperationSerializer()

            batch_operations = BatchOperationCollection(operations=operations)

            queue.put_nowait(dict(func=session.async_post,
                                  kwargs=(dict(url=f'batches',
                                               json=batch_operation_serializer.dumps(batch_operations).data)),
                                  retry=retry))

        for chunk in range(0, max_chunks):
            tasks.append(_get_chunk(queue, results))

        await gather(*tasks)
        return results


def batch_update_members_async(list_id, member_list, max_chunks=9, retry=5):

    loop = get_event_loop()
    queue = Queue()
    responses = loop.run_until_complete(_batch_update_members_async(queue=queue, list_id=list_id,
                                                                    member_list=member_list, max_chunks=max_chunks,
                                                                    retry=retry))

    batch_operation_resource_serializer = BatchOperationResourceSerializer()
    batch_operation_resources = []
    for response in responses:
        batch_operation_resources.append(BatchOperationResource(**batch_operation_resource_serializer
                                                                .load(response.json()).data))

    return batch_operation_resources


async def _get_all_members_async(queue, list_id, count, max_chunks, total_member_count=0, extra_params=None, retry=3):

    tasks = []
    results = []
    extra_params = extra_params or {}

    with MailChimpSession() as session:

        for i in range(0, ceil(total_member_count / count)+1):
            queue.put_nowait(dict(func=session.async_get,
                                  kwargs=dict(url=f'lists/{list_id}/members',
                                              query_parameters=dict(count=count, offset=i * count, **extra_params)),
                                  retry=retry))

        for chunk in range(0, max_chunks):
            tasks.append(_get_chunk(queue, results))

        await gather(*tasks)
        return results


def get_all_members_async(list_id, max_count=1000, max_chunks=9, extra_params=None, retry=3):
    # get list total member count
    while retry > 0:
        try:
            total_member_count = MemberCollectionSerializer().read(list_id, query=extra_params).total_items
        except ClientException as e:
            logger.warning('getting member count for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            sleep(5)
        else:
            count = _calculate_count(total_member_count, max_count, max_chunks)
            if count <= 0:
                return
            loop = get_event_loop()
            queue = Queue()
            responses = loop.run_until_complete(_get_all_members_async(queue=queue, list_id=list_id, count=count,
                                                                       max_chunks=max_chunks,
                                                                       total_member_count=total_member_count,
                                                                       extra_params=extra_params, retry=retry))
            all_members = {}
            for response in responses:
                if not all_members.get('members'):
                    all_members.update(response)
                else:
                    all_members['members'].extend(response['members'])
            return MemberCollection(**all_members)


def _calculate_count(total_member_count, max_count, max_chunks):

    if (total_member_count / (max_count*max_chunks)) > 1:
        return max_count
    else:
        count = ceil(total_member_count/max_chunks)
        return count if count > 0 else 1
