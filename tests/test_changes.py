import unittest
from unittest import mock

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

    def test_returns_412_with_if_none_match_star(self):
        self.app.get(self.changes_uri, headers={
            "If-None-Match": "*"
        }, status=412)

    def test_no_cache_control_is_returned_if_not_configured(self):
        resp = self.app.get(self.changes_uri)
        assert "max-age" not in resp.headers["Cache-Control"]

        resp = self.app.get(self.changes_uri + '?_expected="42"')
        assert "max-age" not in resp.headers["Cache-Control"]

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


class CacheExpiresTest(BaseWebTest, unittest.TestCase):
    changes_uri = '/buckets/monitor/collections/changes/records'

    @classmethod
    def get_app_settings(cls, extras=None):
        settings = super().get_app_settings(extras)
        settings["monitor.changes.record_cache_expires_seconds"] = "60"
        settings["monitor.changes.record_cache_maximum_expires_seconds"] = "3600"
        return settings

    def test_cache_expires_headers_are_supported(self):
        resp = self.app.get(self.changes_uri)
        assert "max-age=60" in resp.headers["Cache-Control"]

    def test_cache_expires_header_is_maximum_with_cache_busting(self):
        resp = self.app.get(self.changes_uri + "?_since=0&_expected=42")
        assert "max-age=3600" in resp.headers["Cache-Control"]

    def test_cache_expires_header_is_default_with_filter(self):
        # The _since just filters on lower bound of timestamps, if data changes
        # we don't want to cache for too long.
        resp = self.app.get(self.changes_uri + "?_since=0")
        assert "max-age=60" in resp.headers["Cache-Control"]

    def test_cache_expires_header_is_default_with_concurrency_control(self):
        # The `If-None-Match` header is just a way to obtain a 304 instead of a 200
        # with an empty list. In the client code [0] it is always used in conjonction
        # with _since={last-etag}
        # [0] https://searchfox.org/mozilla-central/rev/93905b66/services/settings/Utils.jsm#70-73
        headers = {"If-None-Match": '"42"'}
        resp = self.app.get(self.changes_uri + '?_since="42"', headers=headers)
        assert "max-age=60" in resp.headers["Cache-Control"]
