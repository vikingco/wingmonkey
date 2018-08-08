from datetime import datetime
from logging import getLogger

from wingmonkey.lists import get_all_lists
from wingmonkey.async_operations import get_all_members_async

logger = getLogger(__name__)

ADMIN_UNSUBSCRIBE = 'admin'


def import_all_members(list_ids=None, params=None, print_time=None, chunks=9, retry=10, session=None):
    """
    imports all members from all lists using specified filters if None given defaults to all lists
    :param list_ids: list of list ids to get members for
    :param params: dict query parameters
    :param print_time: Bool : print timestamps to console
    :param chunks: int max simultaneous connections to mailchimp server
    :param retry: int : amount of retries after error
    :param session: MailChimpSession
    :return: list of memberlists
    """
    if not list_ids:

        list_collection = get_all_lists(session=session)
        list_ids = [l['id'] for l in list_collection.lists]

    if params:
        formatted_params = dict()
        for key, value in params.items():
            if isinstance(params[key], datetime):
                formatted_params.update({key: datetime.strftime(value, '%Y-%m-%dT%H:%M:%S')})
        params.update(formatted_params)

    # get all members of all lists
    all_members = []
    start = datetime.now()
    for list_id in list_ids:
        member_collection = get_all_members_async(list_id, max_count=1000, max_chunks=chunks, extra_params=params,
                                                  retry=retry, api_endpoint=session.api_endpoint,
                                                  api_key=session.api_key)
        if member_collection:
            all_members.append(member_collection)
    if print_time:
        finish = datetime.now()
        logger.info(f'started: {start}  , finished: {finish}')

    return all_members


def get_unsubscribed_mail_addresses_since(datetime_since=None, list_ids=None, session=None):

    all_unsubscribes_since = import_all_members(list_ids=list_ids, params=dict(since_last_changed=datetime_since,
                                                status='unsubscribed'), chunks=9, retry=10, session=session)
    unique_mail_addresses = set()
    for member_collection in all_unsubscribes_since:
        unique_mail_addresses.update(member['email_address'] for member in member_collection.members
                                     if ADMIN_UNSUBSCRIBE not in member.get('unsubscribe_reason', ''))

    return unique_mail_addresses
