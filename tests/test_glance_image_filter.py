import json

import webob.dec
from tests import test_base

from wafflehaus.iweb.glance.image_filter import obsolete


class FakeWebApp(object):
    def __init__(self, response=None):
        self.response = response
        self.body = response.body

    @webob.dec.wsgify
    def __call__(self, req):
        return self.response


class TestImageFilter(test_base.TestBase):

    def setUp(self):
        self.conf1 = {'enabled': 'true', 'version_metadata': 'version'}
        self.body1 = json.dumps({'images': [
            {"id": 1, "name": "CentOS", "properties": {"version": "1"}},
            {"id": 2, "name": "CentOS", "properties": {"version": "2"}},
            {"id": 3, "name": "Ubuntu", "properties": {"version": "1"}}
        ]})

    def create_response(self, body):
        return webob.response.Response(body=body)

    def test_obsolete_images_are_filtered(self):
        app = FakeWebApp(response=self.create_response(self.body1))

        result = obsolete.filter_factory(self.conf1)(app)
        resp = result.__call__.request('/v1/images', method='GET')
        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(app.body, resp.body)

        body_images = json.loads(resp.body).get("images")
        self.assertEqual(2, len(body_images))
