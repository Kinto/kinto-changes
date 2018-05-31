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
