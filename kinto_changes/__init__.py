import pkg_resources
import pyramid.events
from pyramid.settings import aslist
from kinto.core import events
from .listener import Listener

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version

MONITOR_BUCKET = 'monitor'
MONITOR_BUCKET_PATH = '/buckets/{}'.format(MONITOR_BUCKET)
CHANGES_COLLECTION = 'changes'
CHANGES_COLLECTION_PATH = '{}/collections/{}'.format(
    MONITOR_BUCKET_PATH, CHANGES_COLLECTION)
CHANGES_RECORDS_PATH = '{}/records'.format(CHANGES_COLLECTION_PATH)


def identity(f):
    """Used as a fallback decorator if no statsd configured."""
    return f


def includeme(config):
    settings = config.get_settings()
    collections = settings.get('changes.resources', [])

    # Don't do anything on a migration command.
    # This is helpful because we try to get a snapshot of the database
    # when the application is created. But if we're doing a migrate,
    # there may not be a database.
    if getattr(config.registry, 'command') == 'migrate':
        return

    config.add_api_capability(
        "changes",
        version=__version__,
        description="Track modifications of records in Kinto and store"
                    " the collection timestamps into a specific bucket"
                    " and collection.",
        url="http://kinto.readthedocs.io/en/latest/tutorials/"
        "synchronisation.html#polling-for-remote-changes",
        collections=aslist(collections))

    config.scan('kinto_changes.views')

    listener = Listener(config)

    decorate = identity
    if config.registry.statsd:
        key = 'plugins.kinto_changes'
        decorate = config.registry.statsd.timer(key)

    config.add_subscriber(decorate(listener.track_timestamps),
                          pyramid.events.ApplicationCreated)

    config.add_subscriber(decorate(listener.on_record_changed),
                          events.ResourceChanged,
                          for_resources=('record'))
