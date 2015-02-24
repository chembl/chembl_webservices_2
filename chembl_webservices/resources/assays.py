__author__ = 'mnowotka'

from tastypie.resources import ALL
from tastypie import fields
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
try:
    from chembl_compatibility.models import Assays
except ImportError:
    from chembl_core_model.models import Assays

#-----------------------------------------------------------------------------------------------------------------------

class AssayResource(ChemblModelResource):

    assay_chembl_id = fields.CharField('chembl_id', null=True, blank=True)
    document_chembl_id = fields.CharField('doc__chembl_id', null=True, blank=True)
    target_chembl_id = fields.CharField('target__chembl_id', null=True, blank=True)
    assay_type = fields.CharField('assay_type_id', null=True, blank=True)
    assay_type_description = fields.CharField('assay_type__assay_desc', null=True, blank=True)
    relationship_type = fields.CharField('relationship_type_id', null=True, blank=True)
    relationship_description = fields.CharField('relationship_type__relationship_desc', null=True, blank=True)
    confidence_score = fields.IntegerField('confidence_score_id', null=True, blank=True)
    confidence_description = fields.CharField('confidence_score__description', null=True, blank=True)
    src_id = fields.IntegerField('src_id', null=True, blank=True)
    cell_chembl_id = fields.CharField('cell__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Assays.objects.all()
        excludes = ['assay_id']
        resource_name = 'assay'
        collection_name = 'assays'
        detail_uri_name = 'chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['doc', 'target', 'assay_type', 'relationship_type', 'confidence_score', 'cell']

        fields = (
            'assay_category',
            'assay_cell_type',
            'assay_chembl_id',
            'assay_organism',
            'assay_strain',
            'assay_subcellular_fraction',
            'assay_tax_id',
            'assay_test_type',
            'assay_tissue',
            'assay_type',
            'assay_type_description',
            'bao_format',
            'cell_chembl_id',
            'confidence_description',
            'confidence_score',
            'description',
            'document_chembl_id',
            'relationship_description',
            'relationship_type',
            'src_assay_id',
            'src_id',
            'target_chembl_id',
        )

        filtering = {
            'assay_category' : CHAR_FILTERS,
            'assay_cell_type' : CHAR_FILTERS,
            'assay_chembl_id' : ALL,
            'assay_organism' : CHAR_FILTERS,
            'assay_strain' : CHAR_FILTERS,
            'assay_subcellular_fraction' : CHAR_FILTERS,
            'assay_tax_id' : NUMBER_FILTERS,
            'assay_test_type' : CHAR_FILTERS,
            'assay_tissue' : CHAR_FILTERS,
            'assay_type' : CHAR_FILTERS,
#            'assay_type_description' : ALL,
            'bao_format' : ALL,
            'cell_chembl_id' : CHAR_FILTERS,
#            'confidence_description' : ALL,
            'confidence_score' : NUMBER_FILTERS,
            'description' : CHAR_FILTERS, #TODO: remove from ordering
            'document_chembl_id' : ALL,
#            'relationship_description' : ALL,
            'relationship_type' : CHAR_FILTERS,
            'src_assay_id' : NUMBER_FILTERS,
            'src_id' : NUMBER_FILTERS,
            'target_chembl_id' : ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------
