import mock
import unittest

from . import BaseWebTest
from kinto_changes import includeme

SAMPLE_RECORD = {'data': {'dev-edition': True}}


class RedirectEventsTest(BaseWebTest, unittest.TestCase):
    changes_uri = '/buckets/monitor/collections/changes/records'
    records_uri = '/buckets/blocklists/collections/certificates/records'

    @classmethod
    def make_app(cls, *args, **kwargs):
        with mock.patch('tests.listener.load_from_config') as listener_loader:
            cls.listener = listener_loader.return_value
            return super(RedirectEventsTest, cls).make_app(*args, **kwargs)

    @classmethod
    def get_app_settings(cls, extras=None):
        settings = super(RedirectEventsTest, cls).get_app_settings(extras)
        settings['event_listeners'] = 'tests.listener'
        return settings

    def setUp(self):
        super(RedirectEventsTest, self).setUp()
        self.registry = self.app.app.registry
        self.listener.call_args_list = []

    def test_generate_event(self):
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)
        events = [call[0][0] for call in self.listener.call_args_list]
        monitor_changes_events = [e for e in events
                                  if e.payload.get('bucket_id') == 'monitor' and
                                  e.payload.get('collection_id') == 'changes']
        self.assertEqual(len(monitor_changes_events), 1)
        event = monitor_changes_events[0]

        # ID for buckets/blocklists/collections/certificates
        actual_impacted_record_ids = ['470119ee-115b-8f9c-f56b-afb824183411']

        self.assertEqual(
            [r['new']['id'] for r in event.impacted_records],
            actual_impacted_record_ids
        )

    def test_ignore_event_for_unmonitored(self):
        self.create_collection('foo', 'certificates')
        self.app.post_json('/buckets/foo/collections/certificates/records',
                           SAMPLE_RECORD, headers=self.headers)
        events = [call[0][0] for call in self.listener.call_args_list]
        monitor_changes_events = [e for e in events
                                  if e.payload.get('bucket_id') == 'monitor' and
                                  e.payload.get('collection_id') == 'changes']
        self.assertEqual(len(monitor_changes_events), 0)

    def test_scan_timestamps_on_startup(self):
        self.create_collection('blocklists', 'pinning')
        res = self.app.get('/buckets/blocklists/collections/pinning/records', headers=self.headers)
        last_modified = int(res.headers['ETag'][1:-1])

        old_storage = self.storage
        old_permission = self.permission

        def restore_storage(config):
            """Bring old app's storage/permission (memory-based) over to a new app.

            This lets us test initialization in the case of existing collections."""
            config.registry.storage = old_storage
            config.registry.permission = old_permission

        with mock.patch('tests.test_events', restore_storage):
            self.app = self.make_app({
                'kinto.includes': 'tests.test_events kinto_changes'
            })

        self.app.post_json('/buckets/blocklists/collections/pinning/records', SAMPLE_RECORD,
                           headers=self.headers)
        events = [call[0][0] for call in self.listener.call_args_list]
        monitor_changes_events = [e for e in events
                                  if e.payload.get('bucket_id') == 'monitor' and
                                  e.payload.get('collection_id') == 'changes']
        self.assertEqual(len(monitor_changes_events), 1)
        event = monitor_changes_events[0]

        # ID for buckets/blocklists/collections/pinning
        actual_impacted_record_ids = ['c5b1aefc-bbcc-af1f-df42-73e219236f23']

        self.assertEqual(
            [r['new']['id'] for r in event.impacted_records],
            actual_impacted_record_ids
        )
        self.assertEqual(event.impacted_records[0]['old']['last_modified'], last_modified)


class StatsdTest(BaseWebTest, unittest.TestCase):
    def test_statsd_wraps_subscriber(self):
        config = mock.MagicMock()
        config.settings = {}
        statsd = config.registry.statsd
        statsd_decorate = statsd.timer.return_value

        includeme(config)
        self.assertEqual(statsd.timer.call_args_list[0][0][0], 'plugins.kinto_changes')
        # Check that we're monitoring some calls.
        self.assertTrue(statsd_decorate.call_count >= 2)
