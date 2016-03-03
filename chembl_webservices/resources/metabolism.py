__author__ = 'mnowotka'

from tastypie import fields
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import Metabolism
    from chembl_compatibility.models import MetabolismRefs
except ImportError:
    from chembl_core_model.models import Metabolism
    from chembl_core_model.models import MetabolismRefs

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class MetabolismRefsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = MetabolismRefs.objects.all()
        excludes = []
        resource_name = 'metabolism_ref'
        collection_name = 'metabolism_refs'
        detail_uri_name = 'metref_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = []

        fields = (
            'ref_type',
            'ref_id',
            'ref_url',
        )

        filtering = {
            'ref_type' : CHAR_FILTERS,
            'ref_id' : CHAR_FILTERS,
            'ref_url' : CHAR_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

class MetabolismResource(ChemblModelResource):

    drug_chembl_id = fields.CharField('drug_record__molecule__chembl__chembl_id', null=True, blank=True)
    substrate_chembl_id = fields.CharField('substrate_record__molecule__chembl__chembl_id', null=True, blank=True)
    metabolite_chembl_id = fields.CharField('metabolite_record__molecule__chembl__chembl_id', null=True, blank=True)
    target_chembl_id = fields.CharField('target__chembl__chembl_id', null=True, blank=True)
    metabolism_refs = fields.ToManyField('chembl_webservices.resources.metabolism.MetabolismRefsResource',
        'metabolismrefs_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Metabolism.objects.all()
        excludes = []
        resource_name = 'metabolism'
        collection_name = 'metabolisms'
        detail_uri_name = 'met_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['drug_record', 'drug_record__molecule', 'drug_record__molecule__chembl', 'substrate_record',
                            'substrate_record__molecule', 'substrate_record__molecule__chembl', 'metabolite_record',
                            'metabolite_record__molecule', 'metabolite_record__molecule__chembl', 'target',
                            'target__chembl', 'metabolismrefs_set']

        fields = (
            'met_id',
            'drug_chembl_id',
            'substrate_chembl_id',
            'metabolite_chembl_id',
            'pathway_id',
            'pathway_key',
            'enzyme_name',
            'target_chembl_id',
            'met_conversion',
            'organism',
            'tax_id',
            'met_comment',
            'metabolism_refs',
        )

        filtering = {
            'met_id' : NUMBER_FILTERS,
            'drug_chembl_id' : ALL,
            'substrate_chembl_id' : ALL,
            'metabolite_chembl_id' : ALL,
            'pathway_id' : NUMBER_FILTERS,
            'pathway_key' : CHAR_FILTERS,
            'enzyme_name' : CHAR_FILTERS,
            'target_chembl_id' : ALL,
            'met_conversion' : CHAR_FILTERS,
            'organism' : CHAR_FILTERS,
            'tax_id' : NUMBER_FILTERS,
            'met_comment' : CHAR_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------
