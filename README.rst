=============
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

The list of timestamps is available at ``GET /v1/buckets/monitor/collections/changes/records``.


Advanced options
''''''''''''''''

The changes entries will have a ``host`` attribute, that can be used to
distinguish changes from several Kinto instances.

.. code-block :: ini

    kinto.changes.http_host = website.domain.tld

By default, it will rely on the global setting ``kinto.http_host``.
