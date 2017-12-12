from csv import DictReader

from wingmonkey.merge_fields import get_all_merge_fields, get_merge_field_mapping, match_tag_to_name
from wingmonkey.members import Member
from wingmonkey.enums import MemberStatus

NULL_VALUES = ['NA', 'none', 'None', 'null', 'Null', '']


def import_members_csv(list_id, csv_file, delimiter=',', session=None):
    """
    csv spec:
    email,user_id,first_name,last_name,language,MERGE_FIELDS

    :param list_id: str: id of list members belong to
    :param csv_file: str : csv file ( format has to be to spec as there are some expected fields)
    :param delimiter: str: delimiter used in csv file
    :param session: MailChimpSession
    :return: list of Member instances
    """

    imported_list = []
    merge_field_collection = get_all_merge_fields(list_ids=[list_id], session=session)
    field_mapping = get_merge_field_mapping(merge_field_collection)

    with open(csv_file, 'r') as file:
        csv_reader = DictReader(file, delimiter=delimiter)
        for row in csv_reader:
            row = {key: value for key, value in row.items() if value not in NULL_VALUES and key not in NULL_VALUES}
            mapped = {}
            mapped.update({match_tag_to_name(name, field_mapping) or name: value for name, value in row.items()})
            imported_list.append(mapped)

    member_list = []
    for member in imported_list:

        email_address = member.get('email')
        language = member.get('language')
        merge_fields = {key: value for key, value in member.items() if key in field_mapping.keys()}

        member = validate_member(Member(email_address=email_address, status=MemberStatus.SUBSCRIBED,
                                        list_id=list_id, language=language, merge_fields=merge_fields))
        if member:
            member_list.append(member)

    return member_list


def validate_member(member):
    """
    Checks if Member instance data is ok and corrects of possible to prevent mailchimp errors
    :param member: Member instance
    :return: Cleaned Member instance or None
    """

    if not member.email_address:
        return

    if not member.language:
        member.language = 'English'

    if not member.status:
        member.status = MemberStatus.SUBSCRIBED

    member.merge_fields = {key: value for key, value in member.merge_fields.items() if value not in NULL_VALUES}

    return member
