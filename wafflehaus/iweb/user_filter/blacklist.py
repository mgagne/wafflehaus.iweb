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

        credentials = payload.get('auth', {}).get('passwordCredentials')

        if not credentials:
            self.log.warning('Failed to parse auth credentials')
            return self.app

        username = credentials.get('username')
        self.log.debug('User %s is authenticating', username)
        if username in self.blacklist:
            self.log.warning('User %s is blacklisted', username)
            return webob.exc.HTTPForbidden()

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
