import webob.dec

import wafflehaus.base
import wafflehaus.resource_filter as rf


class ObsoleteFilter(wafflehaus.base.WafflehausBase):

    def __init__(self, app, conf):
        super(ObsoleteFilter, self).__init__(app, conf)
        self.log.name = conf.get('log_name', __name__)
        self.log.info('Starting wafflehaus obsolete image filter middleware')
        self.version_metadata = conf.get('version_metadata', 'build_version')
        self.resource = conf.get('resource',
                                 'GET /images, GET /images/detail, '
                                 'GET /v1/images, GET /v1/images/detail, '
                                 'GET /v2/images, GET /v2/images/detail')
        self.resources = rf.parse_resources(self.resource)

    def _image_version(self, image):
        try:
            return int(
                image.get('properties', {}).get(self.version_metadata, 0))
        except ValueError:
            return 0

    def _filter_obsolete_images(self, req):
        self.log.debug('Filtering obsolete images')
        response = req.get_response(self.app)
        body = response.json
        images = body.get('images')

        latest_images = {}
        for image in list(images):
            name = image['name']
            if name not in latest_images:
                latest_images[name] = image
                continue
            latest_version = self._image_version(latest_images[name])
            current_version = self._image_version(image)
            if current_version > latest_version:
                images.remove(latest_images[name])
                latest_images[name] = image
            else:
                images.remove(image)

        body['images'] = images
        response.json = body

        return response

    @webob.dec.wsgify
    def __call__(self, req):
        if not self.enabled:
            return self.app

        if not rf.matched_request(req, self.resources):
            self.log.debug('Request not matching resource filters (skipping)')
            return self.app

        return self._filter_obsolete_images(req)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def obsolete(app):
        return ObsoleteFilter(app, conf)
    return obsolete
