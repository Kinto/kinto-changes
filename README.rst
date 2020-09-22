Kinto Changes
=============

.. image:: https://img.shields.io/travis/Kinto/kinto-changes.svg
        :target: https://travis-ci.org/Kinto/kinto-changes

.. image:: https://img.shields.io/pypi/v/kinto-changes.svg
        :target: https://pypi.python.org/pypi/kinto-changes

.. image:: https://coveralls.io/repos/Kinto/kinto-changes/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-changes

**kinto-changes** shows the list of collection timestamps, allowing to poll changes
on several collections with one HTTP request.


Install
-------

::

    pip install kinto-changes

Setup
-----

In the `Kinto <http://kinto.readthedocs.io/>`_ settings:

.. code-block :: ini

    kinto.includes = kinto_changes

    # List of buckets/collections to show:
    kinto.changes.resources = /buckets/settings
                              /buckets/blocklists/collections/certificates


Cache Control
'''''''''''''

Like `cache control in Kinto collections <https://kinto.readthedocs.io/en/stable/api/1.x/collections.html#collection-caching>`_, it is possible to configure ``Cache-Control`` headers via some settings:

.. code-block:: ini

    kinto.monitor.changes.record_cache_expires_seconds = 60

If cache busting query parameters then responses can be cached more agressively.
If the setting below is set then a different cache control expiration will be set:

.. code-block:: ini

    kinto.monitor.changes.record_cache_maximum_expires_seconds = 3600


Advanced options
''''''''''''''''

**host**

The changes entries will have a ``host`` attribute, that can be used to
distinguish changes from several Kinto instances.

.. code-block :: ini

    kinto.changes.http_host = website.domain.tld

By default, it will rely on the global setting ``kinto.http_host``.


**_since sanetizing**

When reaching the monitor/changes collection, if the provided ``_since`` query parameter
is too old, we redirect the clients to the full list of changes (ie. without ``_since``).

Set this setting to control the maximum age allowed. Set to ``-1`` to disable redirection.

.. code-block :: ini

    kinto.changes.since_max_age_days = 21


Endpoints
---------

* ``GET /v1/buckets/monitor/collections/changes/records``.

Returns the list of timestamps.

* ``GET /v1/buckets/{bid}/collections/{cid}/changeset?_expected={timestamp}``.

Returns the following response for the collection:

- ``changes``: list of records, optionnally filtered with ``?_since="{timestamp}"``
- ``metadata``: collection attributes
- ``timestamp``: records timestamp

Note: the ``_expected={}`` querystring parameter is mandatory but can contain any
arbitrary value (used for cache busting).
