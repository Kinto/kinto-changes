=============
Kinto Changes
=============

.. image:: https://img.shields.io/travis/kinto/kinto-changes.svg
        :target: https://travis-ci.org/kinto/kinto-changes

.. image:: https://img.shields.io/pypi/v/kinto-changes.svg
        :target: https://pypi.python.org/pypi/kinto-changes

**proof-of-concept**: Plug `Cliquet notifications <http://cliquet.readthedocs.org/en/latest/reference/notifications.html>`_
 to keep track of modified collections.


Install
-------

::

    pip install kinto-changes


Setup
-----

In the Kinto-based application settings:

::

    kinto.includes = kinto_changes

    kinto.event_listeners = kinto_changes.listener
    kinto.event_listeners.changes.resources = <list of resource names>
    kinto.event_listeners.changes.collections = <list of collections names and patterns>


For example, in `Kinto <http://kinto.readthedocs.org/>`_, to be notified of
record updates per collection:

::

    kinto.event_listeners.changes.resources = record
    kinto.event_listeners.changes.collections =
        blocklists:certificates
        settings:*
