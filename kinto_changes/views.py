import colander
from cornice.validators import colander_validator
from pyramid.security import IAuthorizationPolicy
from zope.interface import implementer

import kinto.core
from kinto.authorization import RouteFactory
from kinto.core import resource
from kinto.core import utils as core_utils
from kinto.core.storage import Filter, Sort
from kinto.core.storage.memory import extract_object_set
from kinto.core.storage import exceptions as storage_exceptions
from kinto.core.utils import instance_uri, COMPARISON

from .utils import monitored_collections, changes_object
from . import CHANGESET_PATH, CHANGES_RECORDS_PATH, MONITOR_BUCKET, CHANGES_COLLECTION


class ChangesModel(object):
    id_field = 'id'
    modified_field = 'last_modified'
    deleted_field = 'deleted'
    permissions_field = "__permissions__"

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
        # If the client sends cache busting query parameters, then we can cache more
        # aggressively.
        settings = self.request.registry.settings
        prefix = f'{MONITOR_BUCKET}.{CHANGES_COLLECTION}.record_cache'
        default_expires = settings.get(f'{prefix}_expires_seconds')
        maximum_expires = settings.get(f'{prefix}_maximum_expires_seconds', default_expires)

        has_cache_busting = "_expected" in self.request.GET
        cache_expires = maximum_expires if has_cache_busting else default_expires

        if cache_expires is not None:
            response.cache_expires(seconds=int(cache_expires))


@implementer(IAuthorizationPolicy)
class ChangeSetRoute(RouteFactory):
    """The changeset endpoint should have the same permissions as the collection
    metadata.

    The permission to read records is implicit when metadata are readable.
    """
    def __init__(self, request):
        super().__init__(request)
        bid = request.matchdict["bid"]
        cid = request.matchdict["cid"]
        collection_uri = instance_uri(request, "collection", bucket_id=bid, id=cid)
        # This route context will be the same as when reaching the collection URI.
        self.permission_object_id = collection_uri
        self.required_permission = "read"


changeset = kinto.core.Service(name='collection-changeset',
                               path=CHANGESET_PATH,
                               factory=ChangeSetRoute)


class QuotedTimestamp(colander.SchemaNode):
    """Integer between "" used in _since querystring."""

    schema_type = colander.String
    error_message = "The value should be integer between double quotes."
    validator = colander.Regex('^"([0-9]+?)"$|\\*', msg=error_message)

    def deserialize(self, cstruct=colander.null):
        param = super(QuotedTimestamp, self).deserialize(cstruct)
        if param is colander.drop:
            return param
        return int(param[1:-1])


class ChangeSetQuerystring(colander.MappingSchema):
    _since = QuotedTimestamp(missing=colander.drop)
    _expected = colander.SchemaNode(colander.String())


class ChangeSetSchema(colander.MappingSchema):
    querystring = ChangeSetQuerystring()


@changeset.get(schema=ChangeSetSchema(), permission="read", validators=(colander_validator,))
def get_changeset(request):
    bid = request.matchdict["bid"]
    cid = request.matchdict["cid"]
    bucket_uri = instance_uri(request, "bucket", id=bid)
    collection_uri = instance_uri(request, "collection", bucket_id=bid, id=cid)

    queryparams = request.validated["querystring"]
    filters = []
    if "_since" in queryparams:
        filters = [Filter('last_modified', queryparams["_since"], COMPARISON.GT)]

    storage = request.registry.storage

    # We'll make sure that data isn't changed while we read metadata, changes, etc.
    before = storage.resource_timestamp(resource_name="record", parent_id=collection_uri)
    # Fetch collection metadata.
    metadata = storage.get(resource_name="collection", parent_id=bucket_uri, object_id=cid)
    # Fetch list of changes.
    changes = storage.list_all(
        resource_name="record",
        parent_id=collection_uri,
        filters=filters,
        id_field='id',
        modified_field='last_modified',
        deleted_field='deleted',
        sorting=[Sort('last_modified', -1)]
    )
    # Fetch current collection timestamp.
    timestamp = storage.resource_timestamp(resource_name="record", parent_id=collection_uri)

    # Do not serve inconsistent data.
    if before != timestamp:  # pragma: no cover
        raise storage_exceptions.IntegrityError(message="Inconsistent data. Retry.")

    # Cache control.
    settings = request.registry.settings
    cache_expires = settings.get(f"{bid}.{cid}.record_cache_expires_seconds")
    if cache_expires is not None:
        request.response.cache_expires(seconds=int(cache_expires))

    data = {
        "metadata": metadata,
        "timestamp": timestamp,
        "changes": changes,
    }
    return data
