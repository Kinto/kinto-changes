Changelog
=========


2.1.0 (2019-02-20)
------------------

**New feature**

- Send ``Cache-Control`` headers if cache busting query parameters or concurrency control request headers are sent (#66)

2.0.0 (2019-01-15)
------------------

**Breaking changes**

- Requires Kinto >= 12


1.3.0 (2018-10-15)
------------------

**New feature**

- Add ability to configure cache control headers (#47)


1.2.1 (2018-09-17)
------------------

**Bug fixes**

- Don't do anything during a ``migrate`` command (fixes #43).


1.2.0 (2018-09-06)
------------------

**New feature**

- Events are now generated on the monitor/changes collection (#41).


1.1.1 (2018-04-17)
------------------

**Internal changes**

- Get rid of six


1.1.0 (2017-11-16)
------------------

**Breaking changes**

- Upgrade to Kinto 7


**Bug fixes**

- Disable reify to always get the most accurate timestamp. (#36)


1.0.0 (2017-02-14)
------------------

**Bug fixes**

- Accessing the monitoring collection when no changes occured don't fail anymore (fixes #23)
- The timestamps shown in the monitoring endpoint are now **exactly equal** (never superior anymore)
  to the timestamps of the monitored collections.

**Breaking changes**

* The change endpoint **location is now hard-coded** (``/buckets/monitor/collections/changes/records``)
  and cannot be configured.
* The permissions principals cannot be specified anymore.
  The change endpoint is now **always public**.
* The ``monitor`` bucket and ``changes`` collection are not required anymore and
  are not created anymore.
* ``POST`` and ``DELETE`` are not supported on the changes endpoint anymore.
* Individual entries (eg. ``/buckets/monitor/collections/changes/records/{id}``)
  cannot be accessed anymore.
* The listener was dropped. Configuration must be changed:

Before:

.. code-block :: ini

    kinto.event_listeners = changes
    kinto.event_listeners.changes.use = kinto_changes.listener
    kinto.event_listeners.changes.http_host = website.domain.tld
    kinto.event_listeners.changes.collections = /buckets/settings
                                                /buckets/blocklists/collections/certificates

Now:

.. code-block :: ini

    kinto.changes.http_host = website.domain.tld
    kinto.changes.resources = /buckets/settings
                              /buckets/blocklists/collections/certificates


0.5.0 (2017-01-16)
------------------

- Do not force the timestamp of monitored entries (#27)


0.4.0 (2016-11-07)
------------------

- Add the plugin version in the capability (#20)
- Add collections in the capability (#18)
- Add a specific setting to override global ``http_host`` value (#24)

0.3.0 (2016-05-19)
------------------

- Update to ``kinto.core`` for compatibility with Kinto 3.0. This
  release is no longer compatible with Kinto < 3.0, please upgrade!


0.2.0 (2016-04-25)
------------------

- Addition of the changes capability

0.1.0 (2015-12-22)
------------------

- Initial code.
- Bucket and collection name configuration.
- Changes read permissions configuration.
- Selection of buckets and collections to follow configuration.

