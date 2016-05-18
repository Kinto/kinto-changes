# -*- coding: utf-8 -*-
import os

import webtest
from kinto.tests.core import support as core_support
from kinto.core import utils as core_utils


def get_user_headers(user):
    credentials = "%s:secret" % user
    authorization = 'Basic {0}'.format(core_utils.encode64(credentials))
    return {
        'Authorization': authorization
    }


class BaseWebTest(object):
    config = 'config.ini'

    def __init__(self, *args, **kwargs):
        super(BaseWebTest, self).__init__(*args, **kwargs)
        self.app = self.make_app()

    def setUp(self):
        super(BaseWebTest, self).setUp()
        self.headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:9999'
        }
        self.headers.update(get_user_headers('mat'))

        self.create_collection('blocklists', 'certificates')

    def make_app(self):
        curdir = os.path.dirname(os.path.realpath(__file__))
        app = webtest.TestApp("config:%s" % self.config, relative_to=curdir)
        app.RequestClass = core_support.get_request_class(prefix="v1")
        return app

    def create_collection(self, bucket_id, collection_id):
        bucket_uri = '/buckets/%s' % bucket_id
        self.app.put_json(bucket_uri,
                          {},
                          headers=self.headers)
        collection_uri = bucket_uri + '/collections/%s' % collection_id
        self.app.put_json(collection_uri,
                          {},
                          headers=self.headers)

    def get_record_uri(self, bucket_id, collection_id, record_id):
        return ('/buckets/{bucket_id}/collections/{collection_id}'
                '/records/{record_id}').format(**locals())
