import colander
from pyramid.security import IAuthorizationPolicy
from zope.interface import implementer


from kinto.core import resource
from kinto.core import utils as core_utils
from kinto.core.authorization import RouteFactory
from kinto.core.storage.memory import extract_record_set
from .utils import monitored_collections, changes_record
from . import CHANGES_RECORDS_PATH


class ChangesModel(object):
    id_field = 'id'
    modified_field = 'last_modified'
    deleted_field = 'deleted'

    def __init__(self, request):
        self.request = request
        self.storage = request.registry.storage

        self.__entries = None

    def timestamp(self):
        if not self._entries():
            return core_utils.msec_time()
        max_value = max([e["last_modified"] for e in self._entries()])
        return max_value

    def get_records(self, filters=None, sorting=None, pagination_rules=None,
                    limit=None, include_deleted=False, parent_id=None):
        return extract_record_set(self._entries(), filters=filters, sorting=sorting,
                                  pagination_rules=pagination_rules,
                                  limit=limit)

    def _entries(self):
        if self.__entries is None:
            self.__entries = {}

            for (bucket_id, collection_id) in monitored_collections(self.request.registry):
                collection_uri = core_utils.instance_uri(self.request,
                                                         'collection',
                                                         bucket_id=bucket_id,
                                                         id=collection_id)
                timestamp = self.storage.collection_timestamp(parent_id=collection_uri,
                                                              collection_id='record')

                entry = changes_record(self.request,
                                       bucket_id, collection_id, timestamp)

                self.__entries[entry[self.id_field]] = entry

        return self.__entries.values()


class ChangesSchema(resource.ResourceSchema):
    host = colander.SchemaNode(colander.String())
    bucket = colander.SchemaNode(colander.String())
    collection = colander.SchemaNode(colander.String())

    class Options:
        preserve_unknown = False


@implementer(IAuthorizationPolicy)
class AnonymousRoute(RouteFactory):
    def check_permission(self, principals, bound_perms):
        # Bypass permissions check on /buckets/monitor.
        return True


@resource.register(name='changes',
                   description='List of changes',
                   collection_path=CHANGES_RECORDS_PATH,
                   record_path=None,
                   collection_methods=('GET',),
                   factory=AnonymousRoute)
class Changes(resource.ShareableResource):

    schema = ChangesSchema

    def __init__(self, request, context=None):
        super(Changes, self).__init__(request, context)
        self.model = ChangesModel(request)

    @property
    def timestamp(self):
        return self.model.timestamp()
