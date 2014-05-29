import json

import webob.dec
import webob.request
import webob.response

from wafflehaus.iweb.glance.image_filter import visible
from wafflehaus import tests


class FakeWebApp(object):
    def __init__(self, response=None):
        self.set_response(response)

    def set_response(self, response):
        self.response = response
        self.body = response.body

    @webob.dec.wsgify
    def __call__(self, req):
        return self.response


class RequestContext(object):
    pass


class TestImageFilter(tests.TestCase):

    def setUp(self):
        self.conf1 = {'enabled': 'true',
                      'visible_metadata': 'is_visible'}
        self.conf2 = {'enabled': 'false',
                      'visible_metadata': 'is_visible'}
        self.conf3 = {'enabled': 'true',
                      'visible_metadata': 'is_visible',
                      'roles_whitelist': ''}
        self.body1 = json.dumps({'images': [
            {"id": "0e4cf274-5637-4412-957c-a1584743f41c",
             "name": "Image A",
             "properties": {"version": "1", "is_visible": "0"}},
            {"id": "517f7f5f-37b5-407e-a36d-c9163d606934",
             "name": "Image A",
             "properties": {"version": "2", "is_visible": "1"}},
            {"id": "51a553e6-0b9a-4cff-8e69-56363271575c",
             "name": "Image B",
             "properties": {"version": "1"}},
            {"id": "1fa0356c-73a2-4306-94b9-26c04f49e9f2",
             "name": "Image C",
             "properties": {"is_visible": "invalid"}},
            {"id": "cdbc922d-eabc-4b67-b21e-f88b6dd37c4b",
             "name": "Image D",
             "properties": {}},
        ]})
        self.FILTERED_IMAGES_COUNT = 4
        self.ALL_IMAGES_COUNT = 5
        self.app = FakeWebApp(response=self.create_response(self.body1))

    def create_filter(self, conf):
        return visible.filter_factory(conf)(self.app)

    def create_context(self, **kwargs):
        ctxt = RequestContext()
        for key in kwargs:
            setattr(ctxt, key, kwargs[key])
        return ctxt

    def create_request(self, url, method, context=None):
        req = webob.request.Request.blank(url, method=method)
        if context:
            req.context = context
        return req

    def create_response(self, body):
        return webob.response.Response(body=body)

    def assertImageCount(self, count, resp):
        body_images = json.loads(resp.body).get("images")
        self.assertEqual(count, len(body_images))

    def test_visible_disabled(self):
        """Images are not filtered when disabled."""
        filter = self.create_filter(self.conf2)

        req = self.create_request('/v1/images', method='GET')
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)

    def test_visible_context_not_found(self):
        """Images are filtered if no context is found."""
        filter = self.create_filter(self.conf1)

        req = self.create_request('/v1/images', method='GET')
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_visible_no_roles_whitelist(self):
        """Images are filtered if no roles are whitelisted."""
        filter = self.create_filter(self.conf3)

        ctxt = self.create_context(roles=["_member_"])
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_visible_roles_not_found(self):
        """Images are filtered if no context is found."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context()
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_visible_images_are_filtered_v1(self):
        """Images are filtered (Glance v1)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["_member_"])
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_visible_images_are_filtered_v2(self):
        """Images are filtered (Glance v2)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["_member_"])
        req = self.create_request('/v2/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_visible_roles_whitelist_v1(self):
        """Images are not filtered for whitelisted roles (Glance v1)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["admin"])
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)

    def test_visible_roles_whitelist_v2(self):
        """Images are not filtered for whitelisted roles (Glance v2)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["admin"])
        req = self.create_request('/v2/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)
