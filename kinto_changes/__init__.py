import pkg_resources
from pyramid.settings import aslist

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


def includeme(config):
    settings = config.get_settings()
    collections = settings.get('event_listeners.changes.collections', [])

    config.add_api_capability(
        "changes",
        version=__version__,
        description="Track modifications of records in Kinto and store"
                    " the collection timestamps into a specific bucket"
                    " and collection.",
        url="http://kinto.readthedocs.io/en/latest/tutorials/"
        "synchronisation.html#polling-for-remote-changes",
        collections=aslist(collections))
