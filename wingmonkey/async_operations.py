from asyncio import get_event_loop, gather, sleep as async_sleep, wait_for, TimeoutError, Semaphore
from math import ceil
from time import sleep
from uuid import uuid4
from types import GeneratorType
from collections import namedtuple

from logging import getLogger

from wingmonkey.settings import DEFAULT_MAILCHIMP_ROOT, DEFAULT_MAILCHIMP_API_KEY, DEFAULT_ASYNC_WAIT
from wingmonkey.enums import MAX_MEMBERS_PER_BATCH
from wingmonkey.mailchimp_session import MailChimpSession, ClientException
from wingmonkey.members import (MemberCollection, MemberCollectionSerializer,
                                MemberBatchRequest, MemberBatchRequestSerializer)
from wingmonkey.batch_operations import (BatchOperationResource, BatchOperation,
                                         BatchOperationCollectionSerializer, BatchOperationCollection)

logger = getLogger(__name__)

ProgressStatus = namedtuple('ProgressStatus', 'id total completed last_response_status group_id group_total')


class Progress:
    def __init__(self, callback, total=0, chunk_id=None, group_id=None, group_total=0):
        if not isinstance(callback, GeneratorType):
            raise TypeError(f'callback should be {GeneratorType} but got {type(callback)} instead')

        self.callback = callback
        self.chunk_id = chunk_id if chunk_id is not None else uuid4()
        self.progress_status = ProgressStatus(id=self.chunk_id, total=total, completed=0, last_response_status=None,
                                              group_id=group_id, group_total=group_total)

        next(callback)
        self.send()

    def send(self, step=0, response_status=None):
        self.progress_status = self.progress_status._replace(completed=self.progress_status.completed + step,
                                                             last_response_status=response_status)
        self.callback.send(self.progress_status)

    def reset(self):
        self.progress_status = self.progress_status._replace(completed=0,
                                                             last_response_status='RESET')

    def finish(self):
        self.callback.close()


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
            response = await func(*args, **kwargs)
            json = await response.json()
            status = response.status
            response.close()
            return json, status
        except (ClientException, TimeoutError) as e:
            logger.info('task %s failed. Error: %s , %i retries left', task_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed, log as error
                logger.warning('task %s failed (%s, params: %s %s). Error: %s ', task_id, func, e)
                return None, e.status
            await async_sleep(sleepy_time)


async def _get_response(task, status_only=False, progress=None):
    """
    :param results: list
    :param status_only: Boolean: Only return response status instead of json data
    :param progress: Progress instance
    """

    batch_size = task.pop('batch_size', 0)
    response_json, status = await _async_task(**task)

    if status_only:
        result = status
    else:
        result = response_json

    if progress:
        progress.send(step=batch_size, response_status=status)

    return result


async def _get_responses_async(requests: list, max_concurrency: int, status_only: bool = False,
                               progress: Progress = None):
    tasks = []
    semaphore = Semaphore(max_concurrency)
    async with semaphore:
        for request in requests:
            tasks.append(_get_response(request, status_only=status_only, progress=progress))
        return await gather(*tasks, return_exceptions=True)


async def _calculate_timeout(total_batch_size, retry_count, max_concurrency):
    number_of_batches = total_batch_size / MAX_MEMBERS_PER_BATCH
    timeout_per_batch = DEFAULT_ASYNC_WAIT * retry_count
    return number_of_batches * timeout_per_batch / max_concurrency


async def _update_members_async(list_id, member_list, status_only, max_chunks, retry=3, progress=None,
                                api_endpoint=None, api_key=None):
    requests = []

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        member_batch_request_serializer = MemberBatchRequestSerializer(session=session)

        path = f'lists/{list_id}'
        total_size = len(member_list)

        for j in range(0, total_size, MAX_MEMBERS_PER_BATCH):
            members = member_list[j:j + MAX_MEMBERS_PER_BATCH]
            batch_size = len(members)
            batch_request = MemberBatchRequest(members=members,
                                               update_existing=True)

            requests.append(dict(func=session.async_post,
                                 kwargs=(dict(url=f'{path}',
                                              json=member_batch_request_serializer.dumps(batch_request).data)),
                                 retry=retry, batch_size=batch_size))

        return await wait_for(_get_responses_async(requests, max_concurrency=max_chunks, status_only=status_only,
                                                   progress=progress),
                              timeout=(await _calculate_timeout(total_batch_size=total_size, retry_count=retry,
                                                                max_concurrency=max_chunks)))


def update_members_async(list_id, member_list, status_only=False, max_chunks=10, retry=5, sleepy_time=5, callback=None,
                         chunk_id=None, group_id=None, group_total=0,
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
    progress = None
    responses = None

    if callback:
        try:
            progress = Progress(callback=callback, total=len(member_list), chunk_id=chunk_id,
                                group_id=group_id, group_total=group_total)
        except TypeError as e:
            logger.error(e)
            return

    while retry > 0:
        try:
            responses = loop.run_until_complete(_update_members_async(
                list_id=list_id, member_list=member_list, status_only=status_only, max_chunks=max_chunks, retry=retry,
                progress=progress, api_endpoint=api_endpoint, api_key=api_key))

        except Exception as e:
            logger.info('update_members_async for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            if not retry:
                # we retried and failed
                logger.warning('update_members_async for list %s failed. Error: %s', list_id, e)
                return
            progress.reset()
            sleep(sleepy_time)

        finally:
            if progress:
                progress.finish()
            return [response for response in responses if response is not None]


async def _batch_update_members_async(list_id, member_list, max_chunks, batch_operation_collection_size=25000,
                                      retry=5, api_endpoint=None, api_key=None):

    requests = []

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

            requests.append(dict(func=session.async_post,
                                 kwargs=(dict(url=f'batches',
                                              json=batch_operation_collection_serializer.dumps(batch_operations).data)),
                                 retry=retry))

        return await _get_responses_async(requests, max_concurrency=max_chunks)


def batch_update_members_async(list_id, member_list, max_chunks=9, members_per_call=25000, retry=5, sleepy_time=5,
                               api_endpoint=DEFAULT_MAILCHIMP_ROOT, api_key=DEFAULT_MAILCHIMP_API_KEY):
    loop = get_event_loop()

    while retry > 0:
        try:
            responses = loop.run_until_complete(_batch_update_members_async(
                list_id=list_id, member_list=member_list, max_chunks=max_chunks,
                batch_operation_collection_size=members_per_call, retry=retry,
                api_endpoint=api_endpoint, api_key=api_key))

            batch_operation_resources = []
            for response in responses:
                if isinstance(response, Exception):
                    logger.warning('wingmonkey.get_all_members_async chunk raised exception: %s', response)
                    continue
                if response:
                    batch_operation_resources.append(BatchOperationResource(**response))

            return batch_operation_resources
        except ClientException as e:
            logger.info('creating batch operations for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            if retry < 1:
                # we retried and failed, log as error
                logger.error('creating batch operations for list %s failed. Error: %s', list_id, e)
                return
            sleep(sleepy_time)


async def _get_all_members_async(list_id, count, max_chunks, total_member_count=0, extra_params=None, retry=3,
                                 api_endpoint=None, api_key=None):
    requests = []
    extra_params = extra_params or {}

    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:

        for i in range(ceil(total_member_count / count)):
            requests.append(dict(func=session.async_get,
                                 kwargs=dict(url=f'lists/{list_id}/members',
                                             query_parameters=dict(count=count, offset=i * count, **extra_params)),
                                 retry=retry))

        return await _get_responses_async(requests, max_concurrency=max_chunks)


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
            responses = loop.run_until_complete(_get_all_members_async(list_id=list_id, count=count,
                                                                       max_chunks=max_chunks,
                                                                       total_member_count=total_member_count,
                                                                       extra_params=extra_params, retry=retry,
                                                                       api_endpoint=api_endpoint, api_key=api_key))
            all_members = dict(members=[])
            for response in responses:
                if isinstance(response, Exception):
                    logger.warning('wingmonkey.get_all_members_async chunk raised exception: %s', response)
                    continue
                if response:
                    all_members['members'].extend(response['members'])
            return MemberCollection(**all_members)
        except (ClientException, TimeoutError) as e:
            logger.info('get_all_members_async for list %s failed. Error: %s , %i retries left', list_id, e, retry)
            retry -= 1
            if retry < 1:
                # we retried and failed
                logger.info('get_all_members_async for list %s failed. Error: %s', list_id, e)
                return
            sleep(sleepy_time)


def _calculate_count(total_member_count, max_count, max_chunks):
    if (total_member_count / (max_count * max_chunks)) > 1:
        return max_count
    else:
        count = ceil(total_member_count / max_chunks)
        return count
