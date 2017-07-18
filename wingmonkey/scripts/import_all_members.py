from datetime import datetime

from wingmonkey.lists import ListCollectionSerializer
from wingmonkey.members import get_all_members_async


def import_all_members(params=None, print_time=None, chunks=9, retry=3):
    """
    imports all members from all lists using specified filters
    :param params: dict query parameters
    :param print_time: Bool : print timestamps to console
    :param chunks: int max simultaneous connections to mailchimp server
    :param retry: int : amount of retries after error
    :return: list of memberlists
    """

    list_collection_serializer = ListCollectionSerializer()

    # get list count
    list_count = list_collection_serializer.read(count=1, extra_parameters=dict(fields=['total_items'])).total_items

    # get all lists
    list_collection = list_collection_serializer.read(count=list_count)

    if params:
        formatted_params = dict()
        for key, value in params.items():
            if isinstance(params[key], datetime):
                formatted_params.update({key: datetime.strftime(value, '%Y-%m-%dT%H:%M:%S')})
        params.update(formatted_params)

    # get all members of all lists
    all_members = []
    start = datetime.now()
    for l in list_collection.lists:
        all_members.append(get_all_members_async(l['id'], max_count=1000, max_chunks=chunks, extra_params=params,
                                                 retry=retry))

    if print_time:
        finish = datetime.now()
        print('started: {}  , finished: {}'.format(start, finish))

    return all_members

