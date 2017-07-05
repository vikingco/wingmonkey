from environ import Env, Path
from os import path

env = Env(DEBUG=(bool, False),)

root = Path(__file__) - 2

ROOT = root

ENV_FILE = str(env.path('ENV_FILE', default='.env'))
if path.isfile(ENV_FILE):
    env.read_env(ENV_FILE)
else:
    ENV_FILE = None

MAILCHIMP_API_KEY = env('MAILCHIMP_API_KEY')
DATACENTER = MAILCHIMP_API_KEY.split('-')[1]
MAILCHIMP_ROOT = env('MAILCHIMP_ROOT_URL', default='https://{}.api.mailchimp.com/3.0'.format(DATACENTER))
MAILCHIMP_EXPORT_ROOT = env('MAILCHIMP_EXPORT_ROOT',
                            default='https://{}.api.mailchimp.com/export/1.0'.format(DATACENTER))

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
