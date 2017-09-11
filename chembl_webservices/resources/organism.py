__author__ = 'mnowotka'

from chembl_webservices.core.utils import CHAR_FILTERS
from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import OrganismClass
except ImportError:
    from chembl_core_model.models import OrganismClass

try:
    from chembl_compatibility.models import OrganismSynonyms
except ImportError:
    from chembl_core_model.models import OrganismSynonyms

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()


# ----------------------------------------------------------------------------------------------------------------------


class OrganismSynonymsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = OrganismSynonyms.objects.all()
        excludes = ['tax_id', 'source']
        resource_name = 'organism_synonyms'
        collection_name = 'synonyms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        filtering = {
            'synonyms': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------


class OrganismResource(ChemblModelResource):

    l4_synonyms = fields.ToManyField('chembl_webservices.resources.organism.OrganismSynonymsResource',
                                     'organismsynonyms_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = OrganismClass.objects.all()
        resource_name = 'organism'
        collection_name = 'organisms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = [
            Prefetch('organismsynonyms_set', queryset=OrganismSynonyms.objects.only('pk', 'synonyms',)),
        ]
        filtering = {
            'oc_id': ALL,
            'tax_id': ALL,
            'l1': CHAR_FILTERS,
            'l2': CHAR_FILTERS,
            'l3': CHAR_FILTERS,
            'l4_synonyms': ALL_WITH_RELATIONS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):

        bundles = data['organisms']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

# ----------------------------------------------------------------------------------------------------------------------

    def alter_detail_data_to_serialize(self, request, bundle):

        datas = bundle.data
        datas['l4_synonyms'] = list(set([x.data['synonyms'] for x in datas['l4_synonyms']]))
        return bundle

# ----------------------------------------------------------------------------------------------------------------------
