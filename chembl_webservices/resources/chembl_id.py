__author__ = 'mnowotka'

from tastypie import fields
from tastypie.exceptions import BadRequest
from django.conf.urls import url
from tastypie.utils import trailing_slash
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.resources.molecule import MoleculeResource
from chembl_webservices.resources.assays import AssayResource
from chembl_webservices.resources.target import TargetResource
from chembl_webservices.resources.docs import DocsResource
from chembl_webservices.resources.cell_line import CellLineResource
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup

try:
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet()
except:
    sqs = None

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

molecule = MoleculeResource()
assay = AssayResource()
target = TargetResource()
document = DocsResource()
cell = CellLineResource()

#-----------------------------------------------------------------------------------------------------------------------

class ChemblIdLookupResource(ChemblModelResource):

    resource_url = fields.CharField()
    score = fields.FloatField('score', use_in='search', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = ChemblIdLookup.objects.all()
        resource_name = 'chembl_id_lookup'
        collection_name = 'chembl_id_lookups'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        fields = (
            'chembl_id',
            'entity_type',
            'status',
        )
        filtering = {
            'chembl_id' : CHAR_FILTERS,
            'entity_type': CHAR_FILTERS,
            'status': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['chembl_id_lookups']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

#-----------------------------------------------------------------------------------------------------------------------

    def alter_detail_data_to_serialize(self, request, bundle):
        """
        A hook to alter detail data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for receiving a single bundle of data.
        """
        datas = bundle.data
        detail_name = 'api_dispatch_detail'
        if datas['entity_type'] == 'COMPOUND':
            datas['resource_url'] = molecule._build_reverse_url(detail_name,
                kwargs=molecule.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'ASSAY':
            datas['resource_url'] = assay._build_reverse_url(detail_name,
                kwargs=assay.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'TARGET':
            datas['resource_url'] = target._build_reverse_url(detail_name,
                kwargs=target.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'DOCUMENT':
            datas['resource_url'] = document._build_reverse_url(detail_name,
                kwargs=document.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'CELL':
            kw = cell.resource_uri_kwargs(bundle)
            kw['cell_chembl_id'] = kw['pk']
            del kw['pk']
            datas['resource_url'] = cell._build_reverse_url(detail_name, kwargs=kw)
        return bundle

#-----------------------------------------------------------------------------------------------------------------------

    def get_search_results(self, user_query):

        res = []

        try:
            molecule_qs = molecule._meta.queryset
            molecules = molecule.get_search_results(user_query)
            res.extend([(a, molecules[str(b)]) for (a,b) in
                                            molecule_qs.filter(pk__in=molecules.keys()).values_list('chembl_id', 'pk')])

            target_qs = target._meta.queryset
            targets = target.get_search_results(user_query)
            res.extend([(a, targets[b]) for (a,b) in
                                                target_qs.filter(pk__in=targets.keys()).values_list('chembl_id', 'pk')])

            assay_qs = assay._meta.queryset
            assays = assay.get_search_results(user_query)
            res.extend([(a, assays[str(b)]) for (a,b) in
                                                assay_qs.filter(pk__in=assays.keys()).values_list('chembl_id', 'pk')])

        except Exception as e:
            self.log.error('Searching exception', exc_info=True, extra={'user_query': user_query,})

        return dict(res)

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/search\.(?P<format>xml|json|jsonp|yaml)$" % self._meta.resource_name, self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------