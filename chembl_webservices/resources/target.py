__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from django.conf.urls import url
from tastypie.utils import trailing_slash
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.utils import CHAR_FILTERS, FLAG_FILTERS, NUMBER_FILTERS
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from tastypie.utils import dict_strip_unicode_keys
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary
try:
    from chembl_compatibility.models import TargetType
except ImportError:
    from chembl_core_model.models import TargetType
try:
    from chembl_compatibility.models import TargetComponents
except ImportError:
    from chembl_core_model.models import TargetComponents
try:
    from chembl_compatibility.models import ComponentSequences
except ImportError:
    from chembl_core_model.models import ComponentSequences
try:
    from chembl_compatibility.models import ComponentSynonyms
except ImportError:
    from chembl_core_model.models import ComponentSynonyms
try:
    from chembl_compatibility.models import ComponentXref
except ImportError:
    from chembl_core_model.models import ComponentXref
try:
    from chembl_compatibility.models import TargetXref
except ImportError:
    from chembl_core_model.models import TargetXref
try:
    from chembl_compatibility.models import XrefSource
except ImportError:
    from chembl_core_model.models import XrefSource
try:
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet()
    from haystack.inputs import AutoQuery
    from haystack.query import SQ
except:
    sqs = None

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

available_fields = [f.name for f in TargetDictionary._meta.fields]

# -----------------------------------------------------------------------------------------------------------------------


class TargetComponentSynonyms(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        fields = [
            'component_synonym',
            'syn_type',
        ]
        filtering = {
            'component_synonym': CHAR_FILTERS,
            'syn_type': CHAR_FILTERS,
        }
        queryset = ComponentSynonyms.objects.all()
        resource_name = 'target_component_synonym'
        collection_name = 'target_component_synonyms'

# ----------------------------------------------------------------------------------------------------------------------


class TargetComponentXrefResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        fields = [
            'xref_src_db',
            'xref_id',
            'xref_name',
        ]
        filtering = {
            'xref_src_db': CHAR_FILTERS,
            'xref_id': CHAR_FILTERS,
            'xref_name': CHAR_FILTERS,
        }
        queryset = ComponentXref.objects.all()
        resource_name = 'target_component_xref'
        collection_name = 'target_component_xrefs'

# ----------------------------------------------------------------------------------------------------------------------


class TargetComponentsResource(ChemblModelResource):

    accession = fields.CharField('component__accession', null=True, blank=True)
    component_id = fields.IntegerField('component_id', null=True, blank=True)
    component_type = fields.CharField('component__component_type', null=True, blank=True)
    component_description = fields.CharField('component__description', null=True, blank=True)
    target_component_synonyms = fields.ToManyField('chembl_webservices.resources.target.TargetComponentSynonyms',
                                                   'component__componentsynonyms_set', full=True, null=True, blank=True)
    target_component_xrefs = fields.ToManyField('chembl_webservices.resources.target.TargetComponentXrefResource',
                                                   'component__componentxref_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        fields = [
            'accession',
            'component_id',
            'component_type',
            'relationship',
            'component_description',
        ]
        filtering = {
            'accession': CHAR_FILTERS,
            'component_id': NUMBER_FILTERS,
            'component_type': CHAR_FILTERS,
            'relationship': CHAR_FILTERS,
            'component_description': CHAR_FILTERS,
            'target_component_synonyms': ALL_WITH_RELATIONS,
        }
        prefetch_related = [
            Prefetch('component', queryset=ComponentSequences.objects.only('accession', 'pk', 'component_type',
                                                                           'description')),
            Prefetch('component__componentsynonyms_set'),
            Prefetch('component__componentxref_set'),
        ]
        queryset = TargetComponents.objects.all()
        resource_name = 'target_component'
        collection_name = 'target_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

# ----------------------------------------------------------------------------------------------------------------------


class TargetXRefResource(ChemblModelResource):

    xref_src = fields.CharField('xref_src_db__pk')

    class Meta(ChemblResourceMeta):
        queryset = TargetXref.objects.all()
        resource_name = 'cross_reference'
        collection_name = 'cross_references'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        fields = ('xref_name', 'xref_id', 'xref_src')

# ----------------------------------------------------------------------------------------------------------------------


class TargetResource(ChemblModelResource):

    target_chembl_id = fields.CharField('chembl_id')
    target_type = fields.CharField('target_type_id')
    target_components = fields.ToManyField('chembl_webservices.resources.target.TargetComponentsResource',
                                           'targetcomponents_set', full=True, null=True, blank=True)
    cross_references = fields.ToManyField('chembl_webservices.resources.target.TargetXRefResource',
                                          'targetxref_set', full=True, null=True, blank=True)
    score = fields.FloatField('score', use_in='search', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = TargetDictionary.objects.all() if 'downgraded' not in available_fields else \
            TargetDictionary.objects.filter(downgraded=False)
        excludes = ['tid']
        resource_name = 'target'
        collection_name = 'targets'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name,
                                                         'target_components': 'target_component',
                                                         'target_component_synonyms': 'target_component_synonym'})
        detail_uri_name = 'chembl_id'
        prefetch_related = [
            Prefetch('targetcomponents_set', queryset=TargetComponents.objects.only('pk',
                                                                                    'relationship',
                                                                                    'target',
                                                                                    'component')),
            Prefetch('targetcomponents_set__component', queryset=ComponentSequences.objects.only('accession',
                                                                                                 'pk',
                                                                                                 'component_type',
                                                                                                 'description')),
            Prefetch('targetxref_set', queryset=TargetXref.objects.only(
                'pk',
                'target',
                'xref_name',
                'xref_id',
                'xref_src_db')),
            Prefetch('targetxref_set__xref_src_db', queryset=XrefSource.objects.only('pk')),
            Prefetch('targetcomponents_set__component__componentsynonyms_set'),
            Prefetch('targetcomponents_set__component__componentxref_set'),
        ]

        fields = (
            'organism',
            'tax_id',
            'pref_name',
            'species_group_flag',
            'target_chembl_id',
        )

        filtering = {
            'organism': CHAR_FILTERS,
            'tax_id': NUMBER_FILTERS,
            'pref_name': CHAR_FILTERS,
            'target_type': CHAR_FILTERS,
            'species_group_flag': FLAG_FILTERS,
            'target_chembl_id': ALL,
            'target_components': ALL_WITH_RELATIONS,
        }
        ordering = [
            'organism',
            'tax_id',
            'pref_name',
            'target_type',
            'species_group_flag',
            'target_chembl_id',
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/search\.(?P<format>xml|json|jsonp|yaml)$" % self._meta.resource_name, self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def preprocess_filters(self, filters, for_cache_key=False):
        ret = {}
        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)

            if field_name == 'target_synonym':
                field_name = 'target_components'
                filter_bits = ['target_component_synonyms', 'component_synonym'] + filter_bits
                ret[LOOKUP_SEP.join([field_name] + filter_bits)] = value

            else:
                ret[filter_expr] = value
        return ret

# ----------------------------------------------------------------------------------------------------------------------

    def get_search_results(self, user_query):
        res = []

        try:
            queryset = self._meta.queryset
            model = queryset.model
            res = sqs.models(model).load_all().filter(SQ(content=AutoQuery(user_query))
                                                      | SQ(component_synonyms=AutoQuery(user_query))).order_by('-score')
        except Exception as e:
            self.log.error('Searching exception', exc_info=True, extra={'user_query': user_query, })
        return res

# ----------------------------------------------------------------------------------------------------------------------
