from datetime import datetime
from json import loads
from collections import OrderedDict
from hashlib import md5

from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.settings import DEFAULT_MAILCHIMP_EXPORT_ROOT, DEFAULT_MAILCHIMP_API_KEY, DEFAULT_MAILCHIMP_ROOT
from wingmonkey.enums import MemberStatus, MEMBER_EXPORT_KEYS_MAPPING
from wingmonkey.members import Member
from wingmonkey.merge_fields import MergeFieldCollectionSerializer


def get_all_members(list_id, status=MemberStatus.SUBSCRIBED, segment=None, since=None, hashed=None,
                    api_key=DEFAULT_MAILCHIMP_API_KEY, api_endpoint=DEFAULT_MAILCHIMP_ROOT,
                    api_export_root=DEFAULT_MAILCHIMP_EXPORT_ROOT):
    """
    :param list_id: string: id of list to get members from
    :param status: string: status of members to get (subscribed, unscubscribed, cleaned, pending, transactional)
    :param segment: int: id of segment to get members from
    :param since: datetime: only return members whose data has changed since GMT timestamp
    :param hashed: string: instead of full list data, return a hashed list of email addresses, only 'sha256' supported
    :param api_key: string: mailchimp api key
    :param api_endpoint: string mailchimp regular api root url
    :param api_export_root: string: mailchimp api export root url
    :return: list of Member instances
    """

    query_parameters = dict(apikey=api_key, id=list_id, status=status)

    if segment:
        query_parameters.update(dict(segment=segment))
    if since:
        query_parameters.update(dict(since=datetime.strftime(since, '%Y-%m-%d %H:%M:%S')))
    if hashed:
        query_parameters.update(dict(hashed='sha256'))

    members = list()
    with MailChimpSession(api_endpoint=api_endpoint, api_key=api_key) as session:
        merge_fields = MergeFieldCollectionSerializer(session=session).read(list_id)

    with MailChimpSession(api_endpoint=api_export_root,
                          api_key=api_key).get('list/', query_parameters=query_parameters,
                                               stream=True) as response:
        lines = response.iter_lines()
        header = loads(next(lines))  # first line is a header
        for line in lines:
            values = loads(line)
            member_export_dict = OrderedDict(zip(header, values))
            if not hashed:
                members.append(_convert_member_export_to_member_object(member_export_dict, list_id, status,
                                                                       merge_fields))
            else:
                members.append(member_export_dict['EMAIL_HASH'])

    return members


def _convert_member_export_to_member_object(member_export_dict, list_id, status, list_merge_fields):
    """
    :param member_export_dict: raw member export dictionary
    :param list_id: str: id of list member belongs to
    :param status: string: member status (subscribed, unscubscribed, cleaned, pending, transactional)
    :param list_merge_fields: dict: merge fields defined for list member belongs to
    :return: Member instance
    """

    # generate member id md5 hash
    member_hash = md5()
    member_hash.update(member_export_dict['Email Address'].lower().encode())
    member_id = member_hash.hexdigest()

    # extract and map merge fields
    member_merge_fields = dict()
    for key, value in member_export_dict.items():
        # if the key can not be found in the member_export_keys_mapping it will be a merge field name instead
        if key not in MEMBER_EXPORT_KEYS_MAPPING.keys():
            for field in list_merge_fields.merge_fields:
                if key == field['name']:
                    member_merge_fields.update({field['tag']: value})

    # create Member instance
    member = Member(
        id=member_id,
        email_address=member_export_dict.get('Email Address'),
        status=status,
        merge_fields=member_merge_fields,
        ip_signup=member_export_dict.get('CONFIRM_IP'),
        ip_opt=member_export_dict.get('OPTIN_IP'),
        timestamp_opt=member_export_dict.get('OPTIN_TIME'),
        member_rating=member_export_dict.get('MEMBER_RATING'),
        last_changed=member_export_dict.get('LAST_CHANGED'),
        location={
                  'country_code': member_export_dict.get('CC'),
                  'dstoff': member_export_dict.get('DSTOFF'),
                  'gmtoff': member_export_dict.get('GMTOFF'),
                  'latitude': member_export_dict.get('LATITUDE'),
                  'longitude': member_export_dict.get('LONGITUDE'),
                  'timezone': member_export_dict.get('TIMEZONE')
        },
        list_id=list_id,
        unsubscribe_reason=member_export_dict.get('UNSUB_REASON'),
        unsubscribe_campaign_id=member_export_dict.get('UNSUB_CAMPAIGN_ID'),
        unsubscribe_campaign_title=member_export_dict.get('UNSUB_CAMPAIGN_TITLE')
    )
    return member
