===========
User Filter
===========

Blacklist Filter
---------------------

The blacklist middleware will prevent any blacklisted users
from authenticating to Keystone.

Use Case
~~~~~~~~

You wish to prevent specific users from authenticating to Keystone
without explicitly disabling them.

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

A basic configuration for normal use::

    [filter:user_filter]
    paste.filter_factory = wafflehaus.iweb.user_filter.blacklist:filter_factory
    blacklist = admin nova
    enabled = true

This will prevent the admin and nove users from authenticating to Keystone.
