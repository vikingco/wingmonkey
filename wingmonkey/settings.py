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

DEFAULT_MAILCHIMP_API_KEY = env('DEFAULT_MAILCHIMP_API_KEY', default='SOME-KEY')
DEFAULT_DATACENTER = DEFAULT_MAILCHIMP_API_KEY.split('-')[1]
DEFAULT_MAILCHIMP_ROOT = env('DEFAULT_MAILCHIMP_ROOT_URL',
                             default=f'https://{DEFAULT_DATACENTER}.api.mailchimp.com/3.0')
DEFAULT_MAILCHIMP_EXPORT_ROOT = env('DEFAULT_MAILCHIMP_EXPORT_ROOT',
                                    default=f'https://{DEFAULT_DATACENTER}.api.mailchimp.com/export/1.0')

DEFAULT_BRAND = env('DEFAULT_BRAND', default='Oz, wizard & co')

DEFAULT_PERMISSION_REMINDER = str(f'You get this mail because you are a member of {DEFAULT_BRAND}')
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

MAILCHIMP_MAX_CONNECTIONS = env('MAILCHIMP_MAX_CONNECTIONS', default=10)
DEFAULT_ASYNC_WAIT = 60
