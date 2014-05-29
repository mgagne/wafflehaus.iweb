============
Image Filter
============

Visible Image Filter
--------------------

The visible middleware will filter out non-visible images according
to the 'visible' custom property.

An image is considered non-visible when the value of the 'visible' property
is set to "0". If the property is missing or have any other value,
the image will be considered visible.

Use Case
~~~~~~~~

You wish to filter out obsolete images from the list while still allowing
users to boot from those images.

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

A basic configuration for normal use::

    [filter:image_filter]
    paste.filter_factory = wafflehaus.iweb.glance.image_filter.visible:filter_factory
    visible_metadata = visible
    roles_whitelist = admin superadmin
    enabled = true

This will filter out non-visible images according to the visible property.
Images will not be filtered for users with the 'admin' or 'superadmin' role.
