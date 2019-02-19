import colander
from pyramid.security import IAuthorizationPolicy
from zope.interface import implementer

from kinto.core import resource
from kinto.core import utils as core_utils
from kinto.core.authorization import RouteFactory
from kinto.core.storage.memory import extract_object_set

from .utils import monitored_collections, changes_object
from . import CHANGES_RECORDS_PATH, MONITOR_BUCKET, CHANGES_COLLECTION


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

    def get_objects(self, filters=None, sorting=None, pagination_rules=None,
                    limit=None, include_deleted=False, parent_id=None):
        objs, _ = extract_object_set(objects=self._entries(), filters=filters, sorting=sorting,
                                     pagination_rules=pagination_rules,
                                     limit=limit)
        return objs

    def _entries(self):
        if self.__entries is None:
            self.__entries = {}

            for (bucket_id, collection_id) in monitored_collections(self.request.registry):
                collection_uri = core_utils.instance_uri(self.request,
                                                         'collection',
                                                         bucket_id=bucket_id,
                                                         id=collection_id)
                timestamp = self.storage.resource_timestamp(parent_id=collection_uri,
                                                            resource_name='record')
                entry = changes_object(self.request, bucket_id, collection_id, timestamp)
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
                   plural_path=CHANGES_RECORDS_PATH,
                   object_path=None,
                   plural_methods=('GET',),
                   factory=AnonymousRoute)
class Changes(resource.Resource):

    schema = ChangesSchema

    def __init__(self, request, context=None):
        super(Changes, self).__init__(request, context)
        self.model = ChangesModel(request)

    @property
    def timestamp(self):
        return self.model.timestamp()

    def plural_get(self):
        result = super().plural_get()
        self._handle_cache_expires(self.request.response)
        return result

    def _handle_cache_expires(self, response):
        # If the client sends some querystring parameters or some concurrency-control headers
        # then we do not send a specific cache control header.
        # In production, we set monitor/changes TTL to 1 min and default TTL to 1 hour.
        # With this code and the production config, the clients that don't send cache busting
        # query params get fresh data (1min) and the clients that send quey params and headers
        # are likely to get the cached response for the values they specified.
        has_querystring = len(self.request.GET) > 0
        has_etag_headers = (self.request.headers.get("If-None-Match") or
                            self.request.headers.get("If-Match"))
        setting = '{}.{}.record_cache_expires_seconds'.format(MONITOR_BUCKET, CHANGES_COLLECTION)
        if not has_querystring and not has_etag_headers:
            cache_expires = self.request.registry.settings.get(setting)
            if cache_expires is not None:
                response.cache_expires(seconds=int(cache_expires))
