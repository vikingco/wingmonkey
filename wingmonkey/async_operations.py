from asyncio import get_event_loop, gather, Queue, sleep as async_sleep
from aiohttp import ClientResponse
from math import ceil
from time import sleep
from uuid import uuid4

from logging import getLogger

from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT, DEFAULT_MAILCHIMP_API_KEY
from wingmonkey.enums import MAX_MEMBERS_PER_BATCH
from wingmonkey.mailchimp_session import MailChimpSession, ClientException
from wingmonkey.members import (MemberCollection, MemberCollectionSerializer,
                                MemberBatchRequest, MemberBatchRequestSerializer)
from wingmonkey.batch_operations import (BatchOperationResource, BatchOperation,
                                         BatchOperationCollectionSerializer, BatchOperationCollection)

logger = getLogger(__name__)


async def _async_task(func=None, args=None, kwargs=None, retry=3, sleepy_time=10):
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
            if not retry:
                # we retried and failed, log as error
                logger.error('task %s failed (%s, params: %s %s). Error: %s ', task_id, func, args, kwargs, e)
                return e
            await async_sleep(sleepy_time)


async def _get_response(queue, results, json=False, status_only=False):
    """
    :param queue: asyncio.Queue
    :param results: list
    :param json: Boolean: Return response json instead of whole instance
    :param status_only: Boolean: Only return response status instead of whole instance
    """
    while not queue.empty():
        task = await queue.get()
        response = await _async_task(**task)

        if status_only or type(response) is not ClientResponse:
            results.append(response.status)
        elif json:
            results.append(await response.json())
        else:
            results.append(response)

        if type(response) is ClientResponse:
            response.close()


async def _update_members_async(queue, list_id, member_list, status_only, max_chunks, retry=5,
                                api_endpoint=None, api_key=None):
    tasks = []
    results = []

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        member_batch_request_serializer = MemberBatchRequestSerializer(session=session)

        path = f'lists/{list_id}'

        for j in range(0, len(member_list), MAX_MEMBERS_PER_BATCH):
            batch_request = MemberBatchRequest(members=member_list[j:j + MAX_MEMBERS_PER_BATCH],
                                               update_existing=True)

            queue.put_nowait(dict(func=session.async_post,
                                  kwargs=(dict(url=f'{path}',
                                               json=member_batch_request_serializer.dumps(batch_request).data)),
                                  retry=retry))

        for chunk in range(0, max_chunks):
            tasks.append(_get_response(queue, results, json=True, status_only=status_only))

        await gather(*tasks)
        return results


def update_members_async(list_id, member_list, status_only=False, max_chunks=10, retry=5, sleepy_time=5,
                         api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):

    loop = get_event_loop()
    queue = Queue()

    while retry > 0:
        try:
            responses = loop.run_until_complete(_update_members_async(
                queue=queue, list_id=list_id, member_list=member_list, status_only=status_only, max_chunks=max_chunks,
                retry=retry, api_endpoint=api_endpoint, api_key=api_key))

            return responses
        except ClientException as e:
            logger.warning('update_members_async for list %s failed. Error: %s , %i retries left',
                           list_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed, log as error
                logger.error('update_members_async for list %s failed. Error: %s', list_id, e)
                return
            sleep(sleepy_time)


async def _batch_update_members_async(queue, list_id, member_list, max_chunks, batch_operation_collection_size=25000,
                                      retry=5, api_endpoint=None, api_key=None):

    """
    What happens here:
    1. Split a list of member instances in partial lists of <batch_operation_collection_size>
    2. Per partial list create MemberbatchRequest instance (500 members per instance, as that's the mailchimp limit)
    3. Combine all MemberBatchRequest instances in one BatchOperationCollection instance and add to queue
    4. When this is done for all partial lists process the queue, <max_chunks> tasks at a time
    5. Gather and return results when queue is processed completely
    batch operations reference: http://developer.mailchimp.com/documentation/mailchimp/reference/batches/#%20
    :return: List of BatchOperationResource instances
    """

    tasks = []
    results = []

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        for i in range(0, len(member_list), batch_operation_collection_size):
            partial_list = member_list[i:i + batch_operation_collection_size]

            batches = []
            operations = []
            # split lists into batches of 500 (= max allowed members per batch request)
            for j in range(0, len(partial_list), MAX_MEMBERS_PER_BATCH):
                batch_request = MemberBatchRequest(members=partial_list[j:j + MAX_MEMBERS_PER_BATCH],
                                                   update_existing=True)
                batches.append(batch_request)
            path = f'lists/{list_id}'
            for batch in batches:
                operations.append(BatchOperation(method='POST', path=path,
                                                 body=MemberBatchRequestSerializer(session=session).dumps(batch).data))

            batch_operation_collection_serializer = BatchOperationCollectionSerializer(session=session)

            batch_operations = BatchOperationCollection(operations=operations)

            queue.put_nowait(dict(func=session.async_post,
                                  kwargs=(dict(url=f'batches',
                                               json=batch_operation_collection_serializer.
                                               dumps(batch_operations).data)),
                                  retry=retry))

        for chunk in range(0, max_chunks):
            tasks.append(_get_response(queue, results, json=True))

        await gather(*tasks)
        return results


def batch_update_members_async(list_id, member_list, max_chunks=9, members_per_call=25000, retry=5, sleepy_time=5,
                               api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):

    loop = get_event_loop()
    queue = Queue()

    while retry > 0:
        try:
            responses = loop.run_until_complete(_batch_update_members_async(
                queue=queue, list_id=list_id, member_list=member_list, max_chunks=max_chunks,
                batch_operation_collection_size=members_per_call, retry=retry,
                api_endpoint=api_endpoint, api_key=api_key))

            batch_operation_resources = []
            for response in responses:
                batch_operation_resources.append(BatchOperationResource(**response))

            return batch_operation_resources
        except ClientException as e:
            logger.warning('creating batch operations for list %s failed. Error: %s , %i retries left',
                           list_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed, log as error
                logger.error('creating batch operations for list %s failed. Error: %s', list_id, e)
                return
            sleep(sleepy_time)


async def _get_all_members_async(queue, list_id, count, max_chunks, total_member_count=0, extra_params=None, retry=3,
                                 api_endpoint=None, api_key=None):

    tasks = []
    results = []
    extra_params = extra_params or {}

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        for i in range(ceil(total_member_count / count)):
            queue.put_nowait(dict(func=session.async_get,
                                  kwargs=dict(url=f'lists/{list_id}/members',
                                              query_parameters=dict(count=count, offset=i * count, **extra_params)),
                                  retry=retry))

        for chunk in range(0, max_chunks):
            tasks.append(_get_response(queue, results, json=True))

        await gather(*tasks)
        return results


def get_all_members_async(list_id, max_count=1000, max_chunks=9, extra_params=None, retry=3, sleepy_time=5,
                          api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):

    # get list total member count
    total_member_count = 0
    while retry > 0:
        with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:
            try:
                total_member_count = MemberCollectionSerializer(session=session).read(list_id,
                                                                                      query=extra_params).total_items
                break
            except ClientException as e:
                logger.warning('getting member count for list %s failed. Error: %s , %i retries left',
                               list_id, e, retry)
                retry -= 1
                if not retry:
                    # we retried and failed, log as error
                    logger.error('getting member count for list %s failed. Error: %s', list_id, e)
                    return
                sleep(sleepy_time)

    count = _calculate_count(total_member_count, max_count, max_chunks)
    if count <= 0:
        return
    loop = get_event_loop()
    queue = Queue()
    responses = loop.run_until_complete(_get_all_members_async(queue=queue, list_id=list_id, count=count,
                                                               max_chunks=max_chunks,
                                                               total_member_count=total_member_count,
                                                               extra_params=extra_params, retry=retry,
                                                               api_endpoint=api_endpoint, api_key=api_key))
    all_members = dict(members=[])
    for response in responses:
            all_members['members'].extend(response['members'])
    return MemberCollection(**all_members)


def _calculate_count(total_member_count, max_count, max_chunks):

    if (total_member_count / (max_count*max_chunks)) > 1:
        return max_count
    else:
        count = ceil(total_member_count/max_chunks)
        return count
