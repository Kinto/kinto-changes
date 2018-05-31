import hashlib
from uuid import UUID

from pyramid.settings import aslist

from kinto.core import utils as core_utils


def monitored_collections(registry):
    storage = registry.storage
    resources_uri = aslist(registry.settings.get('changes.resources', ''))
    collections = []

    for resource_uri in resources_uri:
        resource_name, matchdict = core_utils.view_lookup_registry(registry, resource_uri)
        if resource_name == 'bucket':
            # Every collections in this bucket.
            result, _ = storage.get_all(collection_id='collection',
                                        parent_id=resource_uri)
            collections.extend([(matchdict['id'], obj['id']) for obj in result])

        elif resource_name == 'collection':
            collections.append((matchdict['bucket_id'], matchdict['id']))

    return collections


def changes_record(request, http_host, bucket_id, collection_id, timestamp):
    """Generate a record for /buckets/monitor/collections/changes."""
    collection_uri = core_utils.instance_uri(
        request, 'collection', bucket_id=bucket_id, id=collection_id)
    uniqueid = http_host + collection_uri
    identifier = hashlib.md5(uniqueid.encode('utf-8')).hexdigest()
    entry_id = str(UUID(identifier))

    return dict(id=entry_id,
                last_modified=timestamp,
                bucket=bucket_id,
                collection=collection_id,
                host=http_host)
