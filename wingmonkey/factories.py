from factory import Factory, LazyAttribute, Faker, Dict
from wingmonkey.members import Member, generate_member_id


class MemberFactory(Factory):

    class Meta:
        model = Member

    email_address = Faker('email')
    id = LazyAttribute(lambda a: generate_member_id(a.email_address))
    merge_fields = Dict({
        'FNAME': Faker('first_name'),
        'LNAME': Faker('last_name')
    })
