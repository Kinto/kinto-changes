import mock
import unittest

from kinto_changes import __version__ as changes_version
from . import BaseWebTest


SAMPLE_RECORD = {'data': {'dev-edition': True}}


class UpdateChangesTest(BaseWebTest, unittest.TestCase):
    changes_uri = '/buckets/monitor/collections/changes/records'
    records_uri = '/buckets/blocklists/collections/certificates/records'

    def setUp(self):
        super(UpdateChangesTest, self).setUp()
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)

    def test_parent_bucket_and_collection_dont_have_to_exist(self):
        self.app.delete('/buckets/monitor/collections/changes',
                        headers=self.headers, status=(403, 404))
        self.app.get(self.changes_uri)  # Not failing
        self.app.delete('/buckets/monitor',
                        headers=self.headers, status=(403, 404))
        self.app.get(self.changes_uri)  # Not failing

    def test_parent_bucket_and_collection_can_exist(self):
        self.app.put('/buckets/monitor', headers=self.headers)
        resp = self.app.get(self.changes_uri)  # Not failing
        self.assertEqual(len(resp.json['data']), 1)

        self.app.put('/buckets/monitor/collections/changes', headers=self.headers)
        resp = self.app.get(self.changes_uri)  # Not failing
        self.assertEqual(len(resp.json['data']), 1)

    def test_a_change_record_is_updated_per_bucket_collection(self):
        resp = self.app.get(self.changes_uri)
        before_timestamp = resp.json['data'][0]['last_modified']
        before_id = resp.json['data'][0]['id']

        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)

        resp = self.app.get(self.changes_uri)

        after_timestamp = resp.json['data'][0]['last_modified']
        after_id = resp.json['data'][0]['id']
        self.assertEqual(before_id, after_id)
        self.assertNotEqual(before_timestamp, after_timestamp)

    def test_only_collections_specified_in_settings_are_monitored(self):
        resp = self.app.get(self.changes_uri, headers=self.headers)
        change_record = resp.json['data'][0]
        records_uri = '/buckets/default/collections/certificates/records'

        self.app.post_json(records_uri, SAMPLE_RECORD,
                           headers=self.headers)

        resp = self.app.get(self.changes_uri, headers=self.headers)
        after = resp.json['data'][0]
        self.assertEqual(change_record['id'], after['id'])
        self.assertEqual(change_record['last_modified'],
                         after['last_modified'])

    def test_the_resource_configured_can_be_a_collection_uri(self):
        with mock.patch.dict(self.app.app.registry.settings,
                             [('changes.resources',
                               '/buckets/blocklists/collections/certificates')]):
            resp = self.app.get(self.changes_uri)
        self.assertEqual(len(resp.json['data']), 1)

    def test_returns_304_if_no_change_occured(self):
        resp = self.app.get(self.changes_uri)
        before_timestamp = resp.headers["ETag"]
        self.app.get(self.changes_uri,
                     headers={'If-None-Match': before_timestamp},
                     status=304)

    def test_returns_empty_list_if_no_resource_configured(self):
        with mock.patch.dict(self.app.app.registry.settings,
                             [('changes.resources', '')]):
            resp = self.app.get(self.changes_uri)
        self.assertEqual(resp.json['data'], [])

    def test_change_record_has_greater_last_modified_of_collection_of_records(self):
        resp = self.app.post_json(self.records_uri, SAMPLE_RECORD,
                                  headers=self.headers)
        last_modified = resp.json['data']['last_modified']
        resp = self.app.get(self.changes_uri, headers=self.headers)
        change_last_modified = resp.json['data'][0]['last_modified']
        self.assertGreaterEqual(change_last_modified, last_modified)

    def test_record_with_old_timestamp_does_update_changes(self):
        resp = self.app.post_json(self.records_uri, SAMPLE_RECORD,
                                  headers=self.headers)
        old_record = SAMPLE_RECORD.copy()
        old_record['data']['last_modified'] = 42
        self.app.post_json(self.records_uri, old_record, headers=self.headers)

        resp = self.app.get(self.changes_uri, headers=self.headers)
        change_last_modified = resp.json['data'][0]['last_modified']
        self.assertNotEqual(change_last_modified, 42)

    def test_change_record_has_server_host_attribute(self):
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)

        resp = self.app.get(self.changes_uri, headers=self.headers)
        change = resp.json['data'][0]
        self.assertEqual(change['host'], 'www.kinto-storage.org')

    def test_change_record_has_bucket_and_collection_attributes(self):
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)

        resp = self.app.get(self.changes_uri, headers=self.headers)
        change = resp.json['data'][0]
        self.assertEqual(change['bucket'], 'blocklists')
        self.assertEqual(change['collection'], 'certificates')

    def test_changes_capability_exposed(self):
        resp = self.app.get('/')
        capabilities = resp.json['capabilities']
        self.assertIn('changes', capabilities)
        expected = {
            "version": changes_version,
            "description": "Track modifications of records in Kinto and store "
                           "the collection timestamps into a specific bucket "
                           "and collection.",
            "collections": ['/buckets/blocklists'],
            "url": "http://kinto.readthedocs.io/en/latest/tutorials/"
                   "synchronisation.html#polling-for-remote-changes"
        }
        self.assertEqual(expected, capabilities['changes'])
