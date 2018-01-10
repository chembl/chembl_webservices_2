__author__ = 'mnowotka'

from tastypie import fields
from tastypie.utils import trailing_slash
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from tastypie.exceptions import Unauthorized
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import CellDictionary
except ImportError:
    from chembl_core_model.models import CellDictionary
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class CellLineResource(ChemblModelResource):

    cell_chembl_id = fields.CharField('chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = CellDictionary.objects.all()
        resource_name = 'cell_line'
        collection_name = 'cell_lines'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = []

        fields = (
            'cell_description',
            'cell_chembl_id',
            'cell_id',
            'cell_name',
            'cell_source_organism',
            'cell_source_tax_id',
            'cell_source_tissue',
            'cellosaurus_id',
            'clo_id',
            'efo_id',
            'cl_lincs_id',
        )

        filtering = {
            'cell_description': CHAR_FILTERS,
            'cell_chembl_id': CHAR_FILTERS,
            'cell_id': NUMBER_FILTERS,
            'cell_name': CHAR_FILTERS,
            'cell_source_organism': CHAR_FILTERS,
            'cell_source_tax_id': NUMBER_FILTERS,
            'cell_source_tissue': CHAR_FILTERS,
            'cellosaurus_id': CHAR_FILTERS,
            'clo_id': CHAR_FILTERS,
            'efo_id': CHAR_FILTERS,
            'cl_lincs_id': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):

        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<cell_chembl_id_list>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*(;[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<cell_chembl_id_list>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*(;[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<cell_id_list>\d[\d]*(;\d[\d]*)*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<cell_id_list>\d[\d]*(;\d[\d]*)*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<cell_chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<cell_chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<cell_id>\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<cell_id>\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

# ----------------------------------------------------------------------------------------------------------------------

    def get_multiple(self, request, **kwargs):
        """
        Returns a serialized list of resources based on the identifiers
        from the URL.

        Calls ``obj_get`` to fetch only the objects requested. This method
        only responds to HTTP GET.

        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        detail_uri_name = None
        obj_identifiers = None

        for key, value in kwargs.items():
            if key.endswith('_list'):
                detail_uri_name = key.split('_list')[0]
                obj_identifiers = value.split(';')
                break

        objects = []
        not_found = []
        base_bundle = self.build_bundle(request=request)

        for identifier in obj_identifiers:
            try:
                obj, _ = self.cached_obj_get(bundle=base_bundle, **{detail_uri_name: identifier})
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle, for_list=True, **kwargs)
                objects.append(bundle)
            except (ObjectDoesNotExist, Unauthorized):
                not_found.append(identifier)

        object_list = {
            self._meta.collection_name: objects,
        }

        if len(not_found):
            object_list['not_found'] = not_found

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

# ----------------------------------------------------------------------------------------------------------------------
