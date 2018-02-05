from asyncio import get_event_loop, gather, Queue, sleep as async_sleep
from math import ceil
from time import sleep
from uuid import uuid4
from types import GeneratorType
from collections import namedtuple

from logging import getLogger

from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT, DEFAULT_MAILCHIMP_API_KEY
from wingmonkey.enums import MAX_MEMBERS_PER_BATCH
from wingmonkey.mailchimp_session import MailChimpSession, ClientException
from wingmonkey.members import (MemberCollection, MemberCollectionSerializer,
                                MemberBatchRequest, MemberBatchRequestSerializer)
from wingmonkey.batch_operations import (BatchOperationResource, BatchOperation,
                                         BatchOperationCollectionSerializer, BatchOperationCollection)

logger = getLogger(__name__)


ProgressStatus = namedtuple('ProgressStatus', 'id total completed last_response_status group_id group_total')


class Progress:

    def __init__(self, callback, total=0, group_id=None, group_total=0):

        if not isinstance(callback, GeneratorType):
            raise TypeError(f'callback should be {GeneratorType} but got {type(callback)} instead')

        self.callback = callback
        self.progress_status = ProgressStatus(id=uuid4(), total=total, completed=0, last_response_status=None,
                                              group_id=group_id, group_total=group_total)

        next(callback)
        self.send()

    def send(self, step=0, response_status=None):
        self.progress_status = self.progress_status._replace(completed=self.progress_status.completed + step,
                                                             last_response_status=response_status)
        self.callback.send(self.progress_status)

    def finish(self):
        self.callback.close()


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
            response = await func(*args, **kwargs)
            json = await response.json()
            status = response.status
            response.close()
            return json, status
        except ClientException as e:
            logger.info('task %s failed. Error: %s , %i retries left', task_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed, log as error
                logger.error('task %s failed (%s, params: %s %s). Error: %s ', task_id, func, args, kwargs, e)
                return None, e.status
            await async_sleep(sleepy_time)


async def _get_response(queue, results, status_only=False, progress=None):
    """
    :param queue: asyncio.Queue
    :param results: list
    :param status_only: Boolean: Only return response status instead of json data
    :param progress: Progress instance
    """
    while not queue.empty():
        task = await queue.get()
        batch_size = task.pop('batch_size', 0)
        response_json, status = await _async_task(**task)

        if status_only:
            result = status
        else:
            result = response_json

        if result is not None:
            results.append(result)

        if progress:
            progress.send(step=batch_size, response_status=status)


async def _update_members_async(queue, list_id, member_list, status_only, max_chunks, retry=5, progress=None,
                                api_endpoint=None, api_key=None):
    tasks = []
    results = []

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        member_batch_request_serializer = MemberBatchRequestSerializer(session=session)

        path = f'lists/{list_id}'

        for j in range(0, len(member_list), MAX_MEMBERS_PER_BATCH):
            members = member_list[j:j + MAX_MEMBERS_PER_BATCH]
            batch_size = len(members)
            batch_request = MemberBatchRequest(members=members,
                                               update_existing=True)

            queue.put_nowait(dict(func=session.async_post,
                                  kwargs=(dict(url=f'{path}',
                                               json=member_batch_request_serializer.dumps(batch_request).data)),
                                  retry=retry, batch_size=batch_size))

        for chunk in range(0, max_chunks):
            tasks.append(_get_response(queue, results, status_only=status_only,
                                       progress=progress))

        await gather(*tasks)
        return results


def update_members_async(list_id, member_list, status_only=False, max_chunks=10, retry=5, sleepy_time=5, callback=None,
                         group_id=None, group_total=0,
                         api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):
    """

    :param list_id: String:
    :param member_list: List of Member instances
    :param status_only: Boolean: only return status codes instead of full responses
    :param max_chunks: Int: max simultaneous tasks (1 task = 1 connection to mailchimp)
    :param retry: Int: how often to retry when failing
    :param sleepy_time: Int: wait in seconds between retries
    :param callback: GeneratorType: generator class to handle task progress updates
    :param group_id: String: optional id to be able to identify a group of connected sync operations
    :param group_total: Int: optional total count of members to sync in connected operations
    :param api_endpoint: String
    :param api_key: String
    :return: List of responses (either ClientResponse instances, JSON strings or status codes depending on params)
    """

    loop = get_event_loop()
    queue = Queue()
    progress = None

    if callback:
        try:
            progress = Progress(callback=callback, total=len(member_list), group_id=group_id, group_total=group_total)
        except TypeError as e:
            logger.error(e)
            return

    while retry > 0:
        try:
            responses = loop.run_until_complete(_update_members_async(
                queue=queue, list_id=list_id, member_list=member_list, status_only=status_only, max_chunks=max_chunks,
                retry=retry, progress=progress, api_endpoint=api_endpoint, api_key=api_key))

            if progress:
                progress.finish()

            return responses
        except ClientException as e:
            logger.info('update_members_async for list %s failed. Error: %s , %i retries left', list_id, e, retry)
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
            tasks.append(_get_response(queue, results))

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
            logger.info('creating batch operations for list %s failed. Error: %s , %i retries left', list_id, e, retry)
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
            tasks.append(_get_response(queue, results))

        await gather(*tasks)
        return results


def get_all_members_async(list_id, max_count=1000, max_chunks=9, extra_params=None, retry=3, sleepy_time=5,
                          api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):

    session = MailChimpSession(api_endpoint=api_endpoint, api_key=api_key)
    while retry > 0:
        try:
            # get list total member count
            total_member_count = MemberCollectionSerializer(session=session).read(list_id,
                                                                                  query=extra_params).total_items
            session.close()
            count = _calculate_count(total_member_count, max_count, max_chunks)
            if count <= 0:
                return

            # get members
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
        except ClientException as e:
            logger.info('get_all_members_async for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed, log as error
                logger.error('get_all_members_async for list %s failed. Error: %s', list_id, e)
                return
            sleep(sleepy_time)


def _calculate_count(total_member_count, max_count, max_chunks):

    if (total_member_count / (max_count*max_chunks)) > 1:
        return max_count
    else:
        count = ceil(total_member_count/max_chunks)
        return count
