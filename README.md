# wingmonkey
mailchimp api v3 client

mailchimp v3 api reference documentation: http://developer.mailchimp.com/documentation/mailchimp/reference/overview/


### Some usage examples:

#### getting list info


`from wingmonkey.lists import ListSerializer`

`list_serializer = ListSerializer()`

`list_id = 'A_VALID_LIST_ID'`

`my_list = list_serializer.read(list_id=list_id)`

`name = my_list.name`

`total_subscribers = my_list.stats['member_count']`

`unsubscribe_count = my_list.stats['unsubscribe_count']`

#### creating new member

`from wingmonkey.members import Member, MemberSerializer`

`email_address = 'monkeysee@monkey.do'`

`merge_fields = {FNAME: 'Ceasar', LNAME: 'Chimp'}`

`language = 'en'`

`list_id = 'A_VALID_LIST_ID'`

`member_to_add = Member(email_address=email_address, merge_fields=merge_fields, language=language, list_id=list_id)`

`member_serializer = MemberSerializer()`

`newly_added_member = member_serializer.create(list_id=list_id, instance=member_to_add)`

