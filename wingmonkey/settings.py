from environ import Env, Path
from os import path, environ

env = Env(DEBUG=(bool, False),)

root = Path(__file__) - 2

ROOT = root

ENV_FILE = str(env.path('ENV_FILE', default='.env'))
if path.isfile(ENV_FILE):
    env.read_env(ENV_FILE)
else:
    ENV_FILE = None

MAILCHIMP_API_KEY = environ.get('MAILCHIMP_API_KEY')
DATACENTER = MAILCHIMP_API_KEY.split('-')[1]
MAILCHIMP_ROOT = environ.get('MAILCHIMP_ROOT_URL', default=f'https://{DATACENTER}.api.mailchimp.com/3.0')
MAILCHIMP_EXPORT_ROOT = environ.get('MAILCHIMP_EXPORT_ROOT',
                                    default=f'https://{DATACENTER}.api.mailchimp.com/export/1.0')

BRAND = environ.get('BRAND', default='Oz, wizard & co')

DEFAULT_PERMISSION_REMINDER = str(f'You get this mail because you are a member of {BRAND}')
CAMPAIGN_DEFAULTS = environ.get('CAMPAIGN_DEFAULTS', default={
    "from_name": "",
    "from_email": "",
    "subject": "",
    "language": "en"
})
DEFAULT_CONTACT = environ.get('DEFAULT_CONTACT', default={
    "company": "",
    "address1": "",
    "address2": "",
    "city": "",
    "state": "",
    "zip": "",
    "country": "",
    "phone": ""
})
