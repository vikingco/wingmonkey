VISIBILITY_PRIVATE = 'prv'
VISIBILITY_PUBLIC = 'pub'
DEFAULT_RECORD_COUNT = 10

MAX_MEMBERS_PER_BATCH = 500


class MemberStatus(object):

    SUBSCRIBED = 'subscribed'
    UNSUBSCRIBED = 'unsubscribed'
    CLEANED = 'cleaned'
    PENDING = 'pending'
    TRANSACTIONAL = 'transactional'


class HttpMethods(object):

    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class MergeFieldTypes(object):

    TEXT = 'text'
    NUMBER = 'number'
    ADDRESS = 'address'
    PHONE = 'phone'
    DATE = 'date'
    URL = 'url'
    IMAGEURL = 'imageurl'
    RADIO = 'radio'
    DROPDOWN = 'dropdown'
    BIRTHDAY = 'birthday'
    ZIP = 'zip'


class SegmentFieldTypes(object):

    SAVED = 'saved'
    STATIC = 'static'
    FUZZY = 'fuzzy'


MEMBER_EXPORT_KEYS_MAPPING = {
    'Email Address': 'email_address',
    'MEMBER_RATING': 'member_rating',
    'OPTIN_TIME': 'timestamp_opt',
    'OPTIN_IP': 'ip_opt',
    'CONFIRM_TIME': 'confirm_time',
    'CONFIRM_IP': 'ip_signup',
    'LATITUDE': 'latitude',
    'LONGITUDE': 'longitude',
    'GMTOFF': 'gmtoff',
    'DSTOFF': 'dstoff',
    'TIMEZONE': 'timezone',
    'CC': 'country_code',
    'REGION': 'region',
    'LAST_CHANGED': 'last_changed',
    'LEID': 'leid',
    'EUID': 'euid',
    'NOTES': 'notes'
}
