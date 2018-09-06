"""Listener that mirrors events from any collection into the changes collection."""

from kinto.core import utils as core_utils
from kinto.core.events import notify_resource_event, ACTIONS
from .utils import monitored_collections, changes_record, is_monitoring_collection


class Listener(object):
    def __init__(self, config):
        self.registry = config.registry
        self.collection_timestamps = {}

    def track_timestamps(self, event):
        for (bucket_id, collection_id) in monitored_collections(self.registry):
            timestamp = self.get_collection_timestamp(bucket_id, collection_id)
            self.collection_timestamps[(bucket_id, collection_id)] = timestamp

    def get_collection_timestamp(self, bucket_id, collection_id):
        collection_uri = core_utils.instance_uri_registry(self.registry,
                                                          'collection',
                                                          bucket_id=bucket_id,
                                                          id=collection_id)
        return self.registry.storage.collection_timestamp(parent_id=collection_uri,
                                                          collection_id='record')

    def on_record_changed(self, event):
        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        timestamp = event.payload['timestamp']

        if not is_monitoring_collection(self.registry, bucket_id, collection_id):
            return

        for change in event.impacted_records:
            # This might be the first we've seen of this collection.
            old_timestamp = self.collection_timestamps.get((bucket_id, collection_id), None)

            # Synthesize event for /buckets/monitor/collections/changes record.
            new = changes_record(event.request,
                                 bucket_id, collection_id, timestamp)
            old = None
            action = ACTIONS.CREATE
            if old_timestamp:
                action = ACTIONS.UPDATE
                old = changes_record(event.request,
                                     bucket_id, collection_id, old_timestamp)

            resource_data = {'bucket_id': 'monitor', 'collection_id': 'changes', 'id': new['id']}

            notify_resource_event(
                event.request, '/buckets/monitor/collections/changes',
                timestamp, new, action, old=old,
                resource_name='record', resource_data=resource_data
            )

            self.collection_timestamps[(bucket_id, collection_id)] = timestamp
