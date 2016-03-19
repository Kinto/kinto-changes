def includeme(config):
    pass
    config.add_api_capability(
        "changes",
        description="Track modifications of records in Kinto and store"
                    " the collection timestamps into a specific bucket"
                    " and collection.",
        url="http://kinto.readthedocs.org/en/latest/api/1.x/"
            "synchronisation.html#polling-for-remote-changes")
