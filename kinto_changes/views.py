import colander
from pyramid.security import NO_PERMISSION_REQUIRED

from kinto.core import resource
from kinto.core.storage.memory import extract_record_set


class PermissionsModel(object):
    id_field = 'id'
    modified_field = 'last_modified'
    deleted_field = 'deleted'

    def __init__(self, request):
        self.request = request

    def _entries(self):
        # XXX :)
        return [
            {"host":"firefox.settings.services.mozilla.com","last_modified":1486583989669,"bucket":"blocklists","id":"19e79f22-62cf-92e1-c12c-a3b4b9cf51be","collection":"plugins"},
            {"host":"firefox.settings.services.mozilla.com","last_modified":1486576017128,"bucket":"blocklists-preview","id":"3ace9d8e-00b5-a353-7fd5-1f081ff482ba","collection":"plugins"},
            {"host":"firefox.settings.services.mozilla.com","last_modified":1485908438783,"bucket":"blocklists","id":"0e543556-43bf-3139-1fda-2a0068116c6d","collection":"certificates"},
        ]

    def timestamp(self):
        return max([e["last_modified"] for e in self._entries()])

    def get_records(self, filters=None, sorting=None, pagination_rules=None,
                    limit=None, include_deleted=False, parent_id=None):
        return extract_record_set(self._entries(), filters=filters, sorting=sorting,
                                  pagination_rules=pagination_rules,
                                  limit=limit)


class ChangesSchema(resource.ResourceSchema):
    host = colander.SchemaNode(colander.String())
    bucket = colander.SchemaNode(colander.String())
    collection = colander.SchemaNode(colander.String())

    class Options:
        preserve_unknown = False


@resource.register(name='changes',
                   description='List of changes',
                   collection_path='/buckets/monitor/collections/changes/records',
                   record_path=None,
                   collection_methods=('GET',),
                   permission=NO_PERMISSION_REQUIRED)
class Changes(resource.ShareableResource):

    schema = ChangesSchema

    def __init__(self, request, context=None):
        super(Changes, self).__init__(request, context)
        self.model = PermissionsModel(request)
