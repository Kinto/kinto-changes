import hashlib
import six
from uuid import UUID
from pyramid.security import Everyone
from pyramid.settings import aslist
from cliquet.listeners import ListenerBase


class Listener(ListenerBase):
    def __init__(self, collections, changes_bucket, changes_collection):
        super(Listener, self).__init__()
        self.collections = set(collections)
        self.changes_bucket = changes_bucket
        self.changes_collection = changes_collection

    def __call__(self, event):
        registry = event.request.registry

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        bucket_uri = '/buckets/%s' % bucket_id
        collection_uri = u'/buckets/%s/collections/%s' % (bucket_id,
                                                          collection_id)

        collections_uris = {bucket_uri, collection_uri}
        is_matching = collections_uris.intersection(self.collections)
        if self.collections and not is_matching:
            return

        identifier = hashlib.md5(collection_uri.encode('utf-8')).hexdigest()
        record_id = six.text_type(UUID(identifier))

        records = event.impacted_records
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
            object_id=self.changes_bucket,
            record={})

        # Make sure the changes collection exists
        parent_id = '/buckets/%s' % self.changes_bucket
        registry.storage.update(
            parent_id=parent_id,
            collection_id='collection',
            object_id=self.changes_collection,
            record={})

        # Create the new record
        parent_id = '/buckets/%s/collections/%s' % (self.changes_bucket,
                                                    self.changes_collection)
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

    collections = aslist(settings[prefix + 'collections'])

    changes_bucket = settings.get(prefix + 'bucket', 'monitor')
    changes_collection = settings.get(prefix + 'collection', 'changes')

    return Listener(collections, changes_bucket, changes_collection)
