from cliquet.tests.support import unittest

from . import BaseWebTest


class UpdateChangesTest(BaseWebTest, unittest.TestCase):
    def test_record_changes_are_exposed_in_monitor_changes_collection(self):

        self.app.post_json('/buckets/blocklists/collections/certificates/records',
                           {'data': {'dev-edition': True}},
                           headers=self.headers)

        resp = self.app.get('/buckets/monitor/collections/changes/records',
                            headers=self.headers)
        change_record = resp.json['data'][0]

        self.app.post_json('/buckets/blocklists/collections/certificates/records',
                           {'data': {'dev-edition': True}},
                           headers=self.headers)

        resp = self.app.get('/buckets/monitor/collections/changes/records',
                            headers=self.headers)
        after = resp.json['data'][0]
        self.assertEqual(change_record['id'], after['id'])
        self.assertNotEqual(change_record['last_modified'], after['last_modified'])
