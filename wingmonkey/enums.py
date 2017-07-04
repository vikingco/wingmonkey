VISIBILITY_PRIVATE = 'prv'
VISIBILITY_PUBLIC = 'pub'


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
