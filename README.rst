=============
Kinto Changes
=============

.. image:: https://img.shields.io/travis/Kinto/kinto-changes.svg
        :target: https://travis-ci.org/Kinto/kinto-changes

.. image:: https://img.shields.io/pypi/v/kinto-changes.svg
        :target: https://pypi.python.org/pypi/kinto-changes

.. image:: https://coveralls.io/repos/Kinto/kinto-changes/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-changes

**kinto-changes** tracks modifications of records in Kinto and stores the
collection timestamps into a specific bucket and collection.

This plugin is useful to allow for polling on several collections
changes with one HTTP request.


Install
-------

::

    pip install kinto-changes

Setup
-----

In the `Kinto <http://kinto.readthedocs.io/>`_ settings:

::

    kinto.includes = kinto_changes

    kinto.event_listeners = changes
    kinto.event_listeners.changes.use = kinto_changes.listener


Now everytime a record is modified, the list of current timestamps is available
at ``GET /v1/buckets/monitor/collections/changes/records``.


Filter collections
''''''''''''''''''

It is possible to choose which collections are monitored:

::

    kinto.event_listeners.changes.collections = <list of URIs>

For example, to be notified of record updates in the ``certificates`` collection,
or every collections of the ``settings`` bucket:

::

    kinto.event_listeners.changes.collections =
        /buckets/blocklists/collections/certificates
        /buckets/settings


Permissions
'''''''''''

By default the list of timestamps is readable by anonymous users (``system.Everyone``).
But the list of authorized principals can be specified in settings:

::

    kinto.event_listeners.changes.principals =
        system.Authenticated
        group:admins
        twitter:@natim


Advanced options
''''''''''''''''

By default, the list of timestamps is available in the ``changes`` collection in
the ``monitor`` bucket. This can be specified in settings:

::

    kinto.event_listeners.changes.bucket = monitor
    kinto.event_listeners.changes.collection = changes


If specified in settings, the changes will have a ``http_host`` attribute.
This can be used to distinguish changes from several Kinto instances.

::

    kinto.http_host = website.domain.tld
