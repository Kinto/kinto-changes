import hashlib
import six
from uuid import UUID
from pyramid.security import Everyone
from pyramid.settings import aslist
from cliquet.listeners import ListenerBase


class Listener(ListenerBase):
    def __init__(self, collections, resources):
        super(Listener, self).__init__()
        self.collections = set(collections)
        self.resources = set(resources)

    def __call__(self, event):
        registry = event.request.registry

        changes_bucket = registry.settings.get(
            'event_listeners.changes.bucket', 'monitor')
        changes_collection = registry.settings.get(
            'event_listeners.changes.collection', 'changes')

        resource_name = event.payload['resource_name']
        if self.resources and resource_name not in self.resources:
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']

        collection_patterns = {
            '%s:%s' % (bucket_id, collection_id),
            '%s:*' % bucket_id,
            '*:%s' % collection_id
        }
        if self.collections and \
           not collection_patterns.intersection(self.collections):
            return

        records = event.impacted_records

        record_id = six.text_type(UUID(
            hashlib.md5('%s:%s' % (bucket_id, collection_id)).hexdigest()))
        last_modified = 0

        for record in records:
            if 'new' in record:
                # In case we create or update a record.
                record_last_modified = record['new']['last_modified']
            else:
                # In case we delete a record.
                record_last_modified = record['old']['last_modified']

            if record_last_modified > last_modified:
                last_modified = record_last_modified

        # Make sure the monitor bucket exists
        registry.storage.update(
            parent_id='',
            collection_id='bucket',
            object_id=changes_bucket,
            record={})

        # Make sure the changes collection exists
        parent_id = '/buckets/%s' % changes_bucket
        registry.storage.update(
            parent_id=parent_id,
            collection_id='collection',
            object_id=changes_collection,
            record={})

        # Create the new record
        parent_id = '/buckets/%s/collections/%s' % (changes_bucket,
                                                    changes_collection)
        registry.permission.add_principal_to_ace(parent_id, 'read', Everyone)
        registry.storage.update(
            parent_id=parent_id,
            collection_id='record',
            object_id=record_id,
            record={
                'id': record_id,
                'last_modified': last_modified,
                'host': registry.settings.get('http_host'),
                'bucket': bucket_id,
                'collection': collection_id
            })


def load_from_config(config, prefix=''):
    settings = config.get_settings()

    collections = aslist(settings['event_listeners.changes.collections'])
    resources = aslist(settings['event_listeners.changes.resources'])

    return Listener(collections, resources)
