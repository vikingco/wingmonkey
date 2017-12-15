from uuid import uuid4
from marshmallow import fields
from math import ceil

from wingmonkey.enums import HttpMethods
from wingmonkey.mailchimp_session import MailChimpSession, MailChimpSessionSchema
from wingmonkey.mailchimp_base import MailChimpData
from wingmonkey.members import MemberSerializer


class BatchOperationResourceSerializer(MailChimpSessionSchema):

    id = fields.Str()
    status = fields.Str()
    total_operations = fields.Int()
    finished_operations = fields.Int()
    errored_operations = fields.Int()
    submitted_at = fields.DateTime()
    completed_at = fields.DateTime()
    response_body_url = fields.Str()
    _links = fields.List(cls_or_instance=fields.Dict())

    def read(self, batch_id):
        response = self.session.get(f'batches/{batch_id}')
        return BatchOperationResource(
            **BatchOperationResourceSerializer(session=self.session).load(response.json()).data)

    def delete(self, batch_id):
        if self.session.delete(f'batches/{batch_id}'):
            return True


class BatchOperationResource(MailChimpData):

    def __init__(self, id=None, status=None, total_operations=None, finished_operations=None, errored_operations=None,
                 submitted_at=None, completed_at=None, response_body_url=None, _links=None):

        self.id = id
        self.status = status
        self.total_operations = total_operations
        self.finished_operations = finished_operations
        self.errored_operations = errored_operations
        self.submitted_at = submitted_at
        self.completed_at = completed_at
        self.response_body_url = response_body_url
        self._links = _links


class BatchOperationResourceCollectionSerializer(MailChimpSessionSchema):

    batches = fields.List(cls_or_instance=fields.Nested(BatchOperationResourceSerializer))
    total_items = fields.Int()
    _links = fields.List(cls_or_instance=fields.Dict())

    def read(self, chunk_size=250):

        # get count total items
        response = self.session.get('batches', query_parameters=dict(fields=['total_items']))
        total_items = response.json()['total_items']

        # get all batches
        response = self.session.get(
                'batches', query_parameters=dict(count=chunk_size, offset=0)).json()

        for i in range(ceil(total_items/chunk_size)-1):
            response['batches'].extend(self.session.get(
                'batches', query_parameters=dict(count=chunk_size, offset=chunk_size * i)).json()['batches']
            )

        return BatchOperationResourceCollection(**self.load(response).data)


class BatchOperationResourceCollection(MailChimpData):

    def __init__(self, batches=None, total_items=0, _links=None):

        self.batches = batches
        self.total_items = total_items
        self._links = _links


class BatchOperationSerializer(MailChimpSessionSchema):

    method = fields.Str()
    path = fields.Str()
    operation_id = fields.Str()
    params = fields.Dict()
    body = fields.Str()


class BatchOperation(MailChimpData):

    __slots__ = ('method', 'path', 'operation_id', 'params', 'body')

    def __init__(self, method=None, path=None, operation_id=None, params=None, body=None):

        self.method = method
        self.path = path
        self.operation_id = operation_id or uuid4()
        self.params = params or dict()
        self.body = body


class BatchOperationCollectionSerializer(MailChimpSessionSchema):

    operations = fields.List(cls_or_instance=fields.Nested(BatchOperationSerializer))


class BatchOperationCollection(MailChimpData):

    def __init__(self, operations=None):

        self.operations = operations


def _batch_members_operation(list_id, members_list, method, session=None):
    method = method
    member_serializer = MemberSerializer(session=session)
    batch_operation_resource_serializer = BatchOperationResourceSerializer(session=session)
    batch_operations_serializer = BatchOperationCollectionSerializer(session=session)
    operations = list()

    if method == HttpMethods.PATCH:
        # limit serializer to fields that are accepted as PATCH parameters
        member_serializer.only = ('email_address', 'email_type', 'status', 'merge_fields', 'interests', 'language',
                                  'vip', 'location')
        member_serializer._update_fields()

    for member in members_list:

        path = f'lists/{list_id}/members'

        if method == HttpMethods.POST:
            member_serializer.exclude = member.empty_fields
            member_serializer._update_fields()

        elif method == HttpMethods.PATCH:
            # update requests need an existing member id in the url
            path = f'lists/{list_id}/members/{member.id}'

        operations.append(BatchOperation(method=method, path=path, body=member_serializer.dumps(member).data))

    batch_operations = BatchOperationCollection(operations)
    with MailChimpSession() as session:
        response = session.post('batches', json=batch_operations_serializer.dumps(batch_operations).data)

    return BatchOperationResource(**batch_operation_resource_serializer.load(response.json()).data)


def batch_add_members(list_id, members_list, session=None):
    """
    :param list_id: id of list to add members to
    :param members_list: list of Member instances to be added
    :param session: MailChimpSession
    :return: batch operation resource
    """
    return _batch_members_operation(list_id, members_list, HttpMethods.POST, session=session)


def batch_update_members(list_id, members_list, session=None):
    """
    :param list_id: id of list of members to update in
    :param members_list: list of Member instances to be updated
    :param session: MailChimpSession
    :return: batch operation resource
    """

    return _batch_members_operation(list_id, members_list, HttpMethods.PATCH, session=session)


def batch_delete_members(list_id, members_list, session=None):
    """

    :param list_id: id of list of members to delete from
    :param members_list: list of Member instances to be deleted
    :param session: MailChimpSession
    :return: batch operation resource
    """

    return _batch_members_operation(list_id, members_list, HttpMethods.DELETE, session=session)
