import mock
import unittest

from . import BaseWebTest

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

    def test_generate_event(self):
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)
        events = [call[0][0] for call in self.listener.call_args_list]
        monitor_changes_events = [e for e in events
                                  if e.payload.get('bucket_id') == 'monitor' and
                                  e.payload.get('collection_id') == 'changes']
        self.assertEqual(len(monitor_changes_events), 1)
        event = monitor_changes_events[0]
        self.assertEqual([r['new']['id'] for r in event.impacted_records],
                         ['470119ee-115b-8f9c-f56b-afb824183411']  # ID for buckets/blocklists/collections/certificates
        )
