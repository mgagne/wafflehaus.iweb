============
Image Filter
============

Obsolete Image Filter
---------------------

The obsolete middleware will filter out images considered obsolete
according to the build version found in metadata. The filter assumes
images with the same name are from the same "base image" but
with different build versions.

Use Case
~~~~~~~~

You wish to filter out obsolete images from the list while still allowing
users to boot from previous image versions.

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

A basic configuration for normal use::

    [filter:image_filter]
    paste.filter_factory = wafflehaus.iweb.image_filter.obsolete:filter_factory
    version_metadata = build_version
    enabled = true

This will filter out images considered obsolete according to the build version
found in the build_version metadata.
