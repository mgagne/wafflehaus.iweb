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

import webob.dec

import wafflehaus.base
import wafflehaus.resource_filter as rf


class VisibleFilter(wafflehaus.base.WafflehausBase):

    def __init__(self, app, conf):
        super(VisibleFilter, self).__init__(app, conf)
        self.log.name = conf.get('log_name', __name__)
        self.log.info('Starting wafflehaus visible image filter middleware')
        self.visible_metadata = conf.get('visible_metadata', 'visible')
        self.roles_whitelist = conf.get('roles_whitelist', 'admin')
        self.roles_whitelist = [r.strip()
                                for r in self.roles_whitelist.split()]
        self.resource = conf.get('resource',
                                 'GET /images, GET /images/detail, '
                                 'GET /v1/images, GET /v1/images/detail, '
                                 'GET /v2/images, GET /v2/images/detail')
        self.resources = rf.parse_resources(self.resource)

        if not self.roles_whitelist:
            self.log.debug("No whitelisted roles.")

    def _is_visible(self, image):
        return image.get('properties', {}).get(
            self.visible_metadata, "1") != "0"

    def _filter_non_visible_images(self, req):
        self.log.debug('Filtering non-visible images')
        response = req.get_response(self.app)
        body = response.json
        images = body.get('images')

        body['images'] = [i for i in images if self._is_visible(i)]
        response.json = body

        return response

    def _is_whitelisted(self, req):
        """Return True if role is whitelisted or roles cannot be determined."""

        if not self.roles_whitelist:
            return False

        if not hasattr(req, 'context'):
            self.log.info("No context found.")
            return False

        if not hasattr(req.context, 'roles'):
            self.log.info("No roles found in context")
            return False

        roles = req.context.roles
        self.log.debug("Received request from user with roles: %s",
                       ' '.join(roles))
        for key in self.roles_whitelist:
            if key in roles:
                self.log.debug("User role (%s) is whitelisted.", key)
                return True

        return False

    @webob.dec.wsgify
    def __call__(self, req):
        if not self.enabled:
            return self.app

        if not rf.matched_request(req, self.resources):
            self.log.debug("Request not matching resource filters (skipping)")
            return self.app

        if self._is_whitelisted(req):
            return self.app

        return self._filter_non_visible_images(req)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def visible(app):
        return VisibleFilter(app, conf)
    return visible
