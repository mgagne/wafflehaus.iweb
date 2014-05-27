import json

import webob.dec
import webob.request
import webob.response

from wafflehaus.iweb.glance.image_filter import obsolete
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
        self.conf1 = {'enabled': 'true', 'version_metadata': 'version'}
        self.conf2 = {'enabled': 'false'}
        self.conf3 = {'enabled': 'true', 'roles_whitelist': ''}
        self.body1 = json.dumps({'images': [
            {"id": 1, "name": "CentOS", "properties": {"version": "1"}},
            {"id": 2, "name": "CentOS", "properties": {"version": "2"}},
            {"id": 3, "name": "Ubuntu", "properties": {"version": "1"}},
            {"id": 4, "name": "Debian", "properties": {"version": "invalid"}},
            {"id": 5, "name": "Debian", "properties": {"version": "invalid2"}}
        ]})
        self.FILTERED_IMAGES_COUNT = 3
        self.ALL_IMAGES_COUNT = 5
        self.app = FakeWebApp(response=self.create_response(self.body1))

    def create_filter(self, conf):
        return obsolete.filter_factory(conf)(self.app)

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

    def test_obsolete_images_disabled(self):
        """Images are not filtered when disabled."""
        filter = self.create_filter(self.conf2)

        req = self.create_request('/v1/images', method='GET')
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)

    def test_obsolete_images_context_not_found(self):
        """Images are filtered if no context is found."""
        filter = self.create_filter(self.conf1)

        req = self.create_request('/v1/images', method='GET')
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_obsolete_images_no_roles_whitelist(self):
        """Images are filtered if no roles are whitelisted."""
        filter = self.create_filter(self.conf3)

        req = self.create_request('/v1/images', method='GET')
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_obsolete_images_roles_not_found(self):
        """Images are filtered if no context is found."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context()
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_obsolete_images_are_filtered_v1(self):
        """Images are filtered (Glance v1)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["_member_"])
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_obsolete_images_are_filtered_v2(self):
        """Images are filtered (Glance v2)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["_member_"])
        req = self.create_request('/v2/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.response.Response))
        self.assertNotEqual(self.app.body, resp.body)
        self.assertImageCount(self.FILTERED_IMAGES_COUNT, resp)

    def test_obsolete_images_roles_whitelist_v1(self):
        """Images are not filtered for whitelisted roles (Glance v1)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["admin"])
        req = self.create_request('/v1/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)

    def test_obsolete_images_are_not_filtered_for_admin_v2(self):
        """Images are not filtered for whitelisted roles (Glance v2)."""
        filter = self.create_filter(self.conf1)

        ctxt = self.create_context(roles=["admin"])
        req = self.create_request('/v2/images', method='GET', context=ctxt)
        resp = filter.__call__(req)

        self.assertImageCount(self.ALL_IMAGES_COUNT, resp)
