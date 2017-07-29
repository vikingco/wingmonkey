# wingmonkey
mailchimp api v3 client

mailchimp v3 api reference documentation: http://developer.mailchimp.com/documentation/mailchimp/reference/overview/


Some usage examples:

## getting list info


`from wingmonkey.lists import ListSerializer`

`list_serializer = ListSerializer()`

`list_id = 'a_valid_list_id'`

`my_list = list_serializer.read(list_id=list_id)`

`name = my_list.name`

`total_subscribers = my_list.stats['member_count']`

`unsubscribe_count = my_list.stats['unsubscribe_count']`
