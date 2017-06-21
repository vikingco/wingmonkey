from requests_mock import Mocker
from json import dumps

from wingmonkey.mailchimp_account import MailChimpAccountInfo
from wingmonkey.settings import MAILCHIMP_ROOT


def test_mailchimp_account_info():
    expected = {
        "account_id": "NormandySR-1",
        "login_id": "NormandySR-2",
        "account_name": "Systems Alliance",
        "email": "cmdr.shephard@spectre.gov",
        "first_name": "Commander",
        "last_name": "Shephard",
        "username": "CMDRShephard",
        "role": "owner",
        "contact": {
            "company": "Spectre Systems Alliance",
            "addr1": "Spectre Requisitions",
            "addr2": "Presidium",
            "city": "Citadel",
            "state": "",
            "zip": "109831047104719743",
            "country": "Serpent Nebula / Widow"
        },
        "total_subscribers": 9999
    }

    with Mocker() as request_mock:
        request_mock.get('{}/'.format(MAILCHIMP_ROOT), text=dumps(expected))
        account_info = MailChimpAccountInfo()
        assert account_info.serialize() == dumps(expected)
        for key in account_info.__dict__.keys():
            assert account_info.__dict__[key] == expected[key]
