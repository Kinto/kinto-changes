import hashlib
import six
from uuid import UUID

from pyramid.security import Everyone
from pyramid.settings import aslist
from kinto.core.listeners import ListenerBase
from kinto.core.storage import exceptions as storage_exceptions


class Listener(ListenerBase):
    def __init__(self, collections, changes_bucket, changes_collection,
                 changes_principals):
        super(Listener, self).__init__()
        self.collections = set(collections)
        self.changes_bucket = changes_bucket
        self.changes_collection = changes_collection
        self.changes_principals = changes_principals

    def __call__(self, event):
        registry = event.request.registry

        if event.payload['resource_name'] != 'record':
            return

        bucket = event.payload['bucket_id']
        collection = event.payload['collection_id']
        bucket_uri = '/buckets/%s' % bucket
        collection_uri = u'/buckets/%s/collections/%s' % (bucket,
                                                          collection)

        collections_uris = {bucket_uri, collection_uri}
        is_matching = collections_uris.intersection(self.collections)
        if self.collections and not is_matching:
            return

        bucket_id = '/buckets/%s' % self.changes_bucket
        collection_id = '/buckets/%s/collections/%s' % (
            self.changes_bucket, self.changes_collection)

        try:
            # Make sure the monitor bucket exists
            registry.storage.create(collection_id='bucket',
                                    parent_id='',
                                    record={'id': self.changes_bucket})
        except storage_exceptions.UnicityError:
            pass

        try:
            # Make sure the changes collection exists
            registry.storage.create(collection_id='collection',
                                    parent_id=bucket_id,
                                    record={'id': self.changes_collection})
            registry.permission.replace_object_permissions(
                collection_id, {'read': self.changes_principals})
        except storage_exceptions.UnicityError:
            pass

        # Create the new record
        #
        # The record_id is always the same for a given
        # bucket/collection couple. This means the change record will
        # be updated for each record update on a collection.

        host = registry.settings.get('http_host')
        uniqueid = '%s%s' % (host, collection_uri)
        identifier = hashlib.md5(uniqueid.encode('utf-8')).hexdigest()
        record_id = six.text_type(UUID(identifier))
        last_modified = registry.storage.collection_timestamp(
            parent_id=collection_uri, collection_id='record')

        registry.storage.update(
            parent_id=collection_id,
            collection_id='record',
            object_id=record_id,
            record={
                'id': record_id,
                'last_modified': last_modified,
                'host': host,
                'bucket': bucket,
                'collection': collection
            })


def load_from_config(config, prefix=''):
    settings = config.get_settings()

    collections = aslist(settings.get(prefix + 'collections', ''))

    changes_bucket = settings.get(prefix + 'bucket', 'monitor')
    changes_collection = settings.get(prefix + 'collection', 'changes')
    changes_principals = aslist(settings.get(prefix + 'principals', Everyone))

    return Listener(collections, changes_bucket, changes_collection,
                    changes_principals)
