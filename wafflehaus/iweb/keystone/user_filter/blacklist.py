# Copyright 2014 iWeb Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import webob.dec
import webob.exc

import wafflehaus.base
import wafflehaus.resource_filter as rf


class BlacklistFilter(wafflehaus.base.WafflehausBase):

    def __init__(self, app, conf):
        super(BlacklistFilter, self).__init__(app, conf)
        self.log.name = conf.get('log_name', __name__)
        self.log.info('Starting wafflehaus blacklist user filter middleware')
        self.blacklist = conf.get('blacklist', '')
        self.blacklist = [u.strip() for u in self.blacklist.split()]
        self.resource = conf.get('resource',
                                 'POST /v2.0/tokens, POST /v3/auth/tokens')
        self.resources = rf.parse_resources(self.resource)

    def _filter_blacklisted_users(self, req):

        try:
            payload = json.loads(req.body)
        except ValueError:
            self.log.warning('Failed to parse json payload')
            return self.app

        auth = payload.get('auth', {})
        username = None

        # Identity v2.0
        if 'passwordCredentials' in auth:
            self.log.debug('Authenticating with Identity v2.0')
            username = auth.get('passwordCredentials').get('username')
        # Identity v3
        elif 'identity' in auth:
            self.log.debug('Authenticating with Identity v3')
            # Password method
            password_method = auth.get('identity', {}).get('password')
            if password_method:
                self.log.debug('Authenticating with password method')
                username = password_method.get('user', {}).get('name')
            else:
                self.log.warning('Unknown authentication method')
        else:
            self.log.warning('Failed to parse auth credentials')
            return self.app

        self.log.debug('User %s is authenticating', username)
        if username in self.blacklist:
            self.log.info('User %s is blacklisted', username)
            return webob.exc.HTTPForbidden()

        self.log.debug('User %s is not blacklisted', username)
        return self.app

    @webob.dec.wsgify
    def __call__(self, req):
        if not self.enabled:
            return self.app

        if not self.blacklist:
            self.log.debug('No blacklisted users (skipping)')
            return self.app

        if not rf.matched_request(req, self.resources):
            self.log.debug('Request not matching resource filters (skipping)')
            return self.app

        return self._filter_blacklisted_users(req)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def blacklist(app):
        return BlacklistFilter(app, conf)
    return blacklist
