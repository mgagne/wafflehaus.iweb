import mock
import json

import webob.request

from tests import test_base
from wafflehaus.iweb.user_filter import blacklist


class TestUserFilter(test_base.TestBase):

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

    def create_request_body(self, username, version='v2.0'):
        if version == 'v3':
            body = self.body_v2 % {'username': username}
        else:
            body = self.body_v3 % {'username': username}
        return body

    def test_deny_blacklisted_user_v2(self):
        result = blacklist.filter_factory(self.conf1)(self.app)
        body = self.create_request_body('admin', 'v2.0')
        resp = result.__call__.request('/v2.0/tokens', method='POST',
                                       body=body)
        self.assertTrue(isinstance(resp, webob.exc.HTTPException))

    def test_deny_blacklisted_user_v3(self):
        result = blacklist.filter_factory(self.conf1)(self.app)
        body = self.create_request_body('admin', 'v3')
        resp = result.__call__.request('/v2.0/tokens', method='POST',
                                       body=body)
        self.assertTrue(isinstance(resp, webob.exc.HTTPException))

    def test_allow_not_blacklisted_user_v2(self):
        result = blacklist.filter_factory(self.conf1)(self.app)
        body = self.create_request_body('demo', 'v2.0')
        resp = result.__call__.request('/v2.0/tokens', method='POST',
                                       body=body)
        self.assertEqual(self.app, resp)

    def test_allow_not_blacklisted_user_v3(self):
        result = blacklist.filter_factory(self.conf1)(self.app)
        body = self.create_request_body('demo', 'v3')
        resp = result.__call__.request('/v3/auth/tokens', method='POST',
                                       body=body)
        self.assertEqual(self.app, resp)
