import json
import mock

import webob.exc

from wafflehaus.iweb.keystone.user_filter import blacklist
from wafflehaus import tests


class TestUserFilter(tests.TestCase):

    def setUp(self):
        self.app = mock.Mock()
        self.conf1 = {'enabled': 'true', 'blacklist': 'admin nova'}
        self.body_v2 = json.dumps({'auth': {
            "tenantName": "demo",
            "passwordCredentials": {"username": "%(username)s",
                                    "password": "s3cr3t"}}})
        self.body_v3 = json.dumps({"auth": {
            "scope": {
                "project": {
                    "domain": {"id": "default"},
                    "name": "demo"}},
            "identity": {
                "password": {
                    "user": {
                        "domain": {"id": "default"},
                        "password": "s3cr3t",
                        "name": "%(username)s"}},
            "methods": ["password"]}}})

    def create_filter(self, conf):
        return blacklist.filter_factory(conf)(self.app)

    def create_request(self, url, body):
        req = webob.request.Request.blank(url, method='POST')
        req.body = body
        return req

    def test_blacklist_deny_blacklisted_user_v2(self):
        filter = self.create_filter(self.conf1)

        body = self.body_v2 % {'username': 'admin'}
        req = self.create_request('/v2.0/tokens', body=body)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.exc.HTTPException))

    def test_blacklist_deny_blacklisted_user_v3(self):
        filter = self.create_filter(self.conf1)

        body = self.body_v3 % {'username': 'admin'}
        req = self.create_request('/v3/auth/tokens', body=body)
        resp = filter.__call__(req)

        self.assertTrue(isinstance(resp, webob.exc.HTTPException))

    def test_blacklist_allow_not_blacklisted_user_v2(self):
        filter = self.create_filter(self.conf1)

        body = self.body_v2 % {'username': 'demo'}
        req = self.create_request('/v2.0/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_allow_not_blacklisted_user_v3(self):
        filter = self.create_filter(self.conf1)

        body = self.body_v3 % {'username': 'demo'}
        req = self.create_request('/v3/auth/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_disabled_v2(self):
        conf = {'enabled': 'false', 'blacklist': 'admin nova'}
        filter = self.create_filter(conf)

        body = self.body_v2 % {'username': 'admin'}
        req = self.create_request('/v2.0/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_no_blacklist_v2(self):
        conf = {'enabled': 'true', 'blacklist': ''}
        filter = self.create_filter(conf)

        body = self.body_v2 % {'username': 'admin'}
        req = self.create_request('/v2.0/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_unknown_auth(self):
        filter = self.create_filter(self.conf1)

        body = json.dumps({'auth': {}})
        req = self.create_request('/v2.0/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_unknown_auth_v3(self):
        filter = self.create_filter(self.conf1)

        body = json.dumps({'auth': {'identity': {}}})
        req = self.create_request('/v3/auth/tokens', body=body)
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)

    def test_blacklist_junk_body(self):
        """Ignore junk body."""
        filter = self.create_filter(self.conf1)

        req = self.create_request('/v2.0/tokens', body='junk')
        resp = filter.__call__(req)

        self.assertEqual(self.app, resp)
