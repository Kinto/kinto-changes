import unittest

from . import BaseWebTest
from kinto.core.testing import get_user_headers


SAMPLE_RECORD = {'data': {'dev-edition': True}}


class ChangesetViewTest(BaseWebTest, unittest.TestCase):
    records_uri = '/buckets/blocklists/collections/certificates/records'
    changeset_uri = '/buckets/blocklists/collections/certificates/changeset?_expected=42'

    def setUp(self):
        super(ChangesetViewTest, self).setUp()
        self.app.post_json(self.records_uri, SAMPLE_RECORD,
                           headers=self.headers)

    @classmethod
    def get_app_settings(cls, extras=None):
        settings = super().get_app_settings(extras)
        settings["blocklists.certificates.record_cache_expires_seconds"] = 1234
        return settings

    def test_changeset_is_accessible(self):
        resp = self.app.head(self.records_uri, headers=self.headers)
        records_timestamp = int(resp.headers["ETag"][1:-1])

        resp = self.app.get(self.changeset_uri, headers=self.headers)
        data = resp.json

        assert "metadata" in data
        assert "timestamp" in data
        assert "changes" in data
        assert data["metadata"]["id"] == "certificates"
        assert len(data["changes"]) == 1
        assert data["changes"][0]["dev-edition"] is True
        assert data["timestamp"] == records_timestamp

    def test_changeset_can_be_filtered(self):
        resp = self.app.post_json(self.records_uri, {}, headers=self.headers)
        before = resp.json["data"]["last_modified"]
        self.app.post_json(self.records_uri, {}, headers=self.headers)

        resp = self.app.get(self.changeset_uri, headers=self.headers)
        assert len(resp.json["changes"]) == 3

        resp = self.app.get(self.changeset_uri + f'&_since="{before}"', headers=self.headers)
        assert len(resp.json["changes"]) == 1

    def test_changeset_is_not_publicly_accessible(self):
        # By default other users cannot read.
        user_headers = {
            **self.headers,
            **get_user_headers('some-user'),
        }
        self.app.get(self.changeset_uri, status=401)
        self.app.get(self.changeset_uri, headers=user_headers, status=403)

        # Add read permissions to everyone.
        self.app.patch_json("/buckets/blocklists", {
            "permissions": {
                "read": ["system.Everyone"]
            }
        }, headers=self.headers)

        self.app.get(self.changeset_uri, headers=user_headers, status=200)
        self.app.get(self.changeset_uri, status=200)

    def test_timestamp_is_validated(self):
        self.app.get(self.changeset_uri + "&_since=abc", headers=self.headers, status=400)
        self.app.get(self.changeset_uri + "&_since=42", headers=self.headers, status=400)
        self.app.get(self.changeset_uri + '&_since="42"', headers=self.headers)

    def test_expected_param_is_mandatory(self):
        self.app.get(self.changeset_uri.split("?")[0], headers=self.headers, status=400)

    def test_extra_param_is_allowed(self):
        self.app.get(self.changeset_uri + "&_extra=abc", headers=self.headers)

    def test_cache_control_headers_are_set(self):
        resp = self.app.get(self.changeset_uri, headers=self.headers)
        assert resp.headers['Cache-Control'] == 'max-age=1234'
