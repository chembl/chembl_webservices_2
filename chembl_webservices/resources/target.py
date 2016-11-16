__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import BadRequest
from django.conf.urls import url
from tastypie.utils import trailing_slash
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.utils import CHAR_FILTERS, FLAG_FILTERS, NUMBER_FILTERS
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from tastypie.utils import dict_strip_unicode_keys

try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary
    
try:
    from chembl_compatibility.models import TargetComponents
except ImportError:
    from chembl_core_model.models import TargetComponents

try:
    from chembl_compatibility.models import ComponentSynonyms
except ImportError:
    from chembl_core_model.models import ComponentSynonyms

try:
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet()
except:
    sqs = None

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

available_fields = [f.name for f in TargetDictionary._meta.fields]

#-----------------------------------------------------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------------------------------------------------

class TargetComponentsResource(ChemblModelResource):

    accession = fields.CharField('component__accession', null=True, blank=True)
    component_id = fields.IntegerField('component_id', null=True, blank=True)
    component_type = fields.CharField('component__component_type', null=True, blank=True)
    component_description = fields.CharField('component__description', null=True, blank=True)
    target_component_synonyms = fields.ToManyField('chembl_webservices.resources.target.TargetComponentSynonyms',
        'component__componentsynonyms_set', full=True, null=True, blank=True)

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
        queryset = TargetComponents.objects.all()
        resource_name = 'target_component'
        collection_name = 'target_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class TargetResource(ChemblModelResource):

    target_chembl_id = fields.CharField('chembl__chembl_id')
    target_type = fields.CharField('target_type__target_type')
    target_components = fields.ToManyField('chembl_webservices.resources.target.TargetComponentsResource',
        'targetcomponents_set', full=True, null=True, blank=True)
    score = fields.FloatField('score', use_in='search', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = TargetDictionary.objects.all() if 'downgraded' not in available_fields else \
            TargetDictionary.objects.filter(downgraded=False)
        excludes = ['tid']
        resource_name = 'target'
        collection_name = 'targets'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name,
                                                         'target_components':'target_component',
                                                         'target_component_synonyms': 'target_component_synonym'})
        detail_uri_name = 'chembl_id'
        prefetch_related = ['chembl', 'target_type', 'targetcomponents_set', 'targetcomponents_set__component',
                            'targetcomponents_set__component__componentsynonyms_set']

        fields = (
            'organism',
            'pref_name',
            'species_group_flag',
            'target_chembl_id',
        )

        filtering = {
            'organism' : CHAR_FILTERS,
            'pref_name' : CHAR_FILTERS,
            'target_type': CHAR_FILTERS,
            'species_group_flag' : FLAG_FILTERS,
            'target_chembl_id' : ALL,
            'target_components': ALL_WITH_RELATIONS,
        }
        ordering = [
            'organism',
            'pref_name',
            'target_type',
            'species_group_flag',
            'target_chembl_id',
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def get_search_results(self, user_query):

        res = dict()

        try:
            queryset = self._meta.queryset
            model = queryset.model

            res = dict(sqs.models(model).load_all().auto_query(user_query).values_list('pk', 'score'))
            synonyms = sqs.models(ComponentSynonyms).load_all().auto_query(user_query)
            for synonym in synonyms:
                if not synonym.component:
                    continue
                for target in synonym.component.targetdictionary_set.all():
                    key = target.pk
                    if key in res:
                        res[key] = max(res[key], synonym.score)
                    else:
                        res[key] = synonym.score

        except Exception as e:
            self.log.error('Searching exception', exc_info=True, extra={'user_query': user_query,})

        return res

#-----------------------------------------------------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------------------------------------------------

    def build_filters(self, filters=None):

        distinct = False
        if filters is None:
            filters = {}

        qs_filters = {}

        if getattr(self._meta, 'queryset', None) is not None:
            # Get the possible query terms from the current QuerySet.
            query_terms = self._meta.queryset.query.query_terms
        else:
            query_terms = QUERY_TERMS

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if field_name == 'target_synonym':
                field_name = 'target_components'
                filter_bits = ['target_component_synonyms', 'component_synonym'] + filter_bits

            if not field_name in self.fields:
                if filter_expr == 'pk' or filter_expr == self._meta.detail_uri_name:
                    qs_filters[filter_expr] = value
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            if any([x.endswith('_set') for x in lookup_bits]):
                distinct = True
                lookup_bits = map(lambda x: x[0:-4] if x.endswith('_set') else x, lookup_bits)
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters), distinct

#-----------------------------------------------------------------------------------------------------------------------