[![Coverage Status](https://coveralls.io/repos/github/vikingco/wingmonkey/badge.svg)](https://coveralls.io/github/vikingco/wingmonkey)
[![CI Status](https://travis-ci.org/vikingco/wingmonkey.svg?branch=master)](https://travis-ci.org/vikingco/wingmonkey)

# wingmonkey
mailchimp api v3 client

mailchimp v3 api reference documentation: http://developer.mailchimp.com/documentation/mailchimp/reference/overview/


### Some usage examples:

#### getting list info

```
from wingmonkey.lists import ListSerializer

list_serializer = ListSerializer()
list_id = 'A_VALID_LIST_ID'

my_list = list_serializer.read(list_id=list_id)

name = my_list.name
total_subscribers = my_list.stats['member_count']
unsubscribe_count = my_list.stats['unsubscribe_count']
```
#### creating new member

```
from wingmonkey.members import Member, MemberSerializer

email_address = 'monkeysee@monkey.do'
merge_fields = {FNAME: 'Ceasar', LNAME: 'Chimp'}
language = 'en'
list_id = 'A_VALID_LIST_ID'

member_to_add = Member(
                       email_address=email_address, 
                       merge_fields=merge_fields, 
                       language=language, 
                       list_id=list_id
                       )

member_serializer = MemberSerializer()

newly_added_member = member_serializer.create(list_id=list_id, instance=member_to_add)
```

#### get all members of a list

```

from wingmonkey.async_operations import get_all_members_async
from datetime import datetime, timedelta

list_id = 'A_VALID_LIST_ID'
```

* all members
```
all_list_members = get_all_members_async(list_id=list_id)
```

* all members updated since specific date (take care to use the correct string format for datetime)
```
date_since = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%dT%H:%M:%S')
extra_params = {'since_last_changed': date_since }
all_updated_members_since_yesterday = get_all_members_async(list_id=list_id, extra_params=extra_params)
```

#### batch update of a large list of members 
* This will return a list of corresponding batch operation resources (1 for every 500 members)
http://developer.mailchimp.com/documentation/mailchimp/reference/batches/#create-post_batches
http://developer.mailchimp.com/documentation/mailchimp/reference/lists/#create-post_lists_list_id

```
from wingmonkey.async_operations import batch_update_members_async
list_id = 'A_VALID_LIST_ID'
member_list = [A_LIST_OF_MEMBER_INSTANCES]

batch_operation_resource_list = batch_update_members_async(list_id=list_id, member_list=member_list)
```
