from environ import Env, Path

env = Env(DEBUG=(bool, False),)

root = Path(__file__)
env.read_env()

ROOT = root()
MAILCHIMP_API_KEY = env('MAILCHIMP_API_KEY')
DATACENTER = MAILCHIMP_API_KEY.split('-')[1]
MAILCHIMP_ROOT = env('MAILCHIMP_ROOT_URL', default='https://{}.api.mailchimp.com/3.0'.format(DATACENTER))

BRAND = env('BRAND', default='Oz, wizard & co')

DEFAULT_PERMISSION_REMINDER = str('You get this mail because you are a member of {}'.format(BRAND))
CAMPAIGN_DEFAULTS = env.dict('CAMPAIGN_DEFAULTS', default={
    "from_name": "",
    "from_email": "",
    "subject": "",
    "language": "en"
})
DEFAULT_CONTACT = env.dict('DEFAULT_CONTACT', default={
    "company": "",
    "address1": "",
    "address2": "",
    "city": "",
    "state": "",
    "zip": "",
    "country": "",
    "phone": ""
})
