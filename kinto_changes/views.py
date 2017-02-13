import hashlib
import six
from uuid import UUID

import colander
from pyramid.security import NO_PERMISSION_REQUIRED, IAuthorizationPolicy
from pyramid.settings import aslist
from zope.interface import implementer


from kinto.core import resource
from kinto.core import utils as core_utils
from kinto.core.authorization import RouteFactory
from kinto.core.storage.memory import extract_record_set


class PermissionsModel(object):
    id_field = 'id'
    modified_field = 'last_modified'
    deleted_field = 'deleted'

    def __init__(self, request):
        self.request = request
        self.storage = request.registry.storage

        settings = request.registry.settings
        self.http_host = settings.get('http_host') or ''
        self.resources_uri = aslist(settings.get('kinto.event_listeners.changes.collections',
                                    settings.get('kinto.changes.resources', '')))

    def _entries(self):
        entries = []

        for (bucket_id, collection_id) in self._monitored_collections():
            bucket_uri = core_utils.instance_uri(self.request, 'bucket', id=bucket_id)
            collection_uri = core_utils.instance_uri(self.request,
                                                     'collection',
                                                     bucket_id=bucket_id,
                                                     id=collection_id)
            timestamp = self.storage.collection_timestamp(parent_id=bucket_uri,
                                                          collection_id=collection_id)

            uniqueid = (self.http_host + collection_uri)
            identifier = hashlib.md5(uniqueid.encode('utf-8')).hexdigest()
            entry_id = six.text_type(UUID(identifier))

            entry = dict(id=entry_id,
                         last_modified=timestamp,
                         bucket=bucket_id,
                         collection=collection_id,
                         host=self.http_host)

            entries.append(entry)

        return entries

    def _monitored_collections(self):
        collections = []

        for resource_uri in self.resources_uri:
            resource_name, matchdict = core_utils.view_lookup(self.request, resource_uri)
            if resource_name == 'bucket':
                # Every collections in this bucket.
                result, count = self.storage.get_all(collection_id='collection',
                                                     parent_id=resource_uri)
                collections.extend([(matchdict['id'], obj['id']) for obj in result])

            elif resource_name == 'collection':
                collections.append((matchdict['bucket_id'], matchdict['id']))

        return collections

    def timestamp(self):
        entries = self._entries()
        if entries:
            return max([e["last_modified"] for e in entries])
        return core_utils.timestamp()

    def get_records(self, filters=None, sorting=None, pagination_rules=None,
                    limit=None, include_deleted=False, parent_id=None):
        return extract_record_set(self._entries(), filters=filters, sorting=sorting,
                                  pagination_rules=pagination_rules,
                                  limit=limit)


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
                   collection_path='/buckets/monitor/collections/changes/records',
                   record_path=None,
                   collection_methods=('GET',),
                   permission=NO_PERMISSION_REQUIRED,
                   factory=AnonymousRoute)
class Changes(resource.ShareableResource):

    schema = ChangesSchema

    def __init__(self, request, context=None):
        super(Changes, self).__init__(request, context)
        self.model = PermissionsModel(request)
