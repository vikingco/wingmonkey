from uuid import uuid4
from marshmallow import Schema, fields

from wingmonkey.enums import HttpMethods
from wingmonkey.mailchimp_session import MailChimpSession
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.members import MemberSerializer

session = MailChimpSession()


class BatchOperationResourceSerializer(Schema):

    id = fields.Str()
    status = fields.Str()
    total_operations = fields.Int()
    finished_operations = fields.Int()
    errored_operations = fields.Int()
    submitted_at = fields.DateTime()
    completed_at = fields.DateTime()
    response_body_url = fields.Str()

    def read(self, batch_id):
        response = session.get('batches/{}'.format(batch_id))
        return BatchOperationResource(**BatchOperationResourceSerializer().load(response.json()).data)

    def delete(self, batch_id):
        if session.delete('batches/{}'.format(batch_id)):
            return True


class BatchOperationResource(MailChimpData):

    def __init__(self, id=None, status=None, total_operations=None, finished_operations=None, errored_operations=None,
                 submitted_at=None, completed_at=None, response_body_url=None):

        self.id = id
        self.status = status
        self.total_operations = total_operations
        self.finished_operations = finished_operations
        self.errored_operations = errored_operations
        self.submitted_at = submitted_at
        self.completed_at = completed_at
        self.response_body_url = response_body_url


class BatchOperationSerializer(Schema):

    method = fields.Str()
    path = fields.Str()
    operation_id = fields.Str()
    params = fields.Dict()
    body = fields.Str()


class BatchOperation(MailChimpData):

    def __init__(self, method=None, path=None, operation_id=None, params=None, body=None):

        self.method = method
        self.path = path
        self.operation_id = operation_id or uuid4()
        self.params = params or dict()
        self.body = body


class BatchOperationsCollectionSerializer(Schema):

    operations = fields.List(cls_or_instance=fields.Nested(BatchOperationSerializer))


class BatchOperationsCollection(MailChimpData):

    def __init__(self, operations=None):

        self.operations = operations


def _batch_members_operation(list_id, members_list, method):
    method = method
    path = 'lists/{}/members'.format(list_id)
    member_serializer = MemberSerializer()
    batch_operation_resource_serializer = BatchOperationResourceSerializer()
    batch_operations_serializer = BatchOperationsCollectionSerializer()
    operations = list()

    if method == HttpMethods.PATCH:
        # limit serializer to fields that are accepted as PATCH parameters
        member_serializer.only = ('email_address', 'email_type', 'status', 'merge_fields', 'interests', 'language',
                                  'vip', 'location')
        member_serializer._update_fields()

    for member in members_list:

        if method == HttpMethods.POST:
            member_serializer.exclude = member.empty_fields
            member_serializer._update_fields()

        elif method == HttpMethods.PATCH:
            # update requests need an existing member id in the url
            path += '/{}'.format(member.id)

        operations.append(BatchOperation(method=method, path=path, body=member_serializer.dumps(member).data))

    batch_operations = BatchOperationsCollection(operations)
    response = session.post('batches', json=batch_operations_serializer.dumps(batch_operations).data)

    return BatchOperationResource(**batch_operation_resource_serializer.load(response.json()).data)


def batch_add_members(list_id, members_list):
    """
    :param list_id: id of list to add members to
    :param members_list: list of Member instances to be added
    :return: batch operation resource
    """
    return _batch_members_operation(list_id, members_list, HttpMethods.POST)


def batch_update_members(list_id, members_list):
    """
    :param list_id: id of list of members to update in
    :param members_list: list of Member instances to be updated
    :return: batch operation resource
    """

    return _batch_members_operation(list_id, members_list, HttpMethods.PATCH)


def batch_delete_members(list_id, members_list):
    """

    :param list_id: id of list of members to delete from
    :param members_list: list of Member instances to be deleted
    :return: batch operation resource
    """

    return _batch_members_operation(list_id, members_list, HttpMethods.DELETE)
