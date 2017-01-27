__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
try:
    from chembl_compatibility.models import Activities
except ImportError:
    from chembl_core_model.models import Activities

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class ActivityResource(ChemblModelResource):

    bao_format = fields.CharField('assay__bao_format__bao_id', null=True, blank=True)
    bao_endpoint = fields.CharField('bao_endpoint__bao_id', null=True, blank=True)
    data_validity_comment = fields.CharField('data_validity_comment__description', null=True, blank=True)
    document_chembl_id = fields.CharField('doc__chembl__chembl_id', null=True, blank=True)
    molecule_chembl_id = fields.CharField('molecule__chembl__chembl_id', null=True, blank=True)
    target_chembl_id = fields.CharField('assay__target__chembl__chembl_id', null=True, blank=True)
    target_pref_name = fields.CharField('assay__target__pref_name', null=True, blank=True)
    target_organism = fields.CharField('assay__target__organism', null=True, blank=True)
    assay_chembl_id = fields.CharField('assay__chembl__chembl_id', null=True, blank=True)
    assay_type = fields.CharField('assay__assay_type__assay_type', null=True, blank=True)
    src_id = fields.IntegerField('assay__src__src_id', null=True, blank=True)
    assay_description = fields.CharField('assay__description', null=True, blank=True)
    document_year = fields.IntegerField('doc__year', null=True, blank=True)
    document_journal = fields.CharField('doc__journal', null=True, blank=True)
    record_id = fields.IntegerField('record__record_id', null=True, blank=True)
    canonical_smiles = fields.CharField('molecule__compoundstructures__canonical_smiles', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Activities.objects.all()
        resource_name = 'activity'
        collection_name = 'activities'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['assay', 'assay__chembl', 'assay__target', 'assay__target__chembl', 'assay__assay_type',
                            'assay__src', 'doc', 'doc__chembl',
                            'molecule', 'molecule__chembl', 'molecule__compoundstructures',
                            'data_validity_comment',
                            'record']
        fields = (
            'activity_comment',
            'activity_id',
            'assay_chembl_id',
            'assay_description',
            'assay_type',
            'src_id',
            'bao_endpoint',
            'bao_format'
            'canonical_smiles',
            'data_validity_comment',
            'document_journal',
            'document_year',
            'document_chembl_id',
            'molecule_chembl_id',
            'pchembl_value',
            'potential_duplicate',
            'published_relation',
            'published_type',
            'published_units',
            'published_value',
            'qudt_units',
            'record_id',
            'standard_flag',
            'standard_relation',
            'standard_type',
            'standard_units',
            'standard_value',
            'target_pref_name',
            'target_organism',
            'uo_units',
        )
        filtering = {
            'activity_comment': CHAR_FILTERS,
            'activity_id': NUMBER_FILTERS,
            'assay_chembl_id': ALL,
            'assay_description': CHAR_FILTERS,
            'assay_type': CHAR_FILTERS,
            'bao_endpoint': ALL,
            'target_chembl_id': CHAR_FILTERS,
            'canonical_smiles': FLAG_FILTERS,
            'data_validity_comment': ALL,
            'document_chembl_id': ALL,
            'document_journal': CHAR_FILTERS,
            'document_year': NUMBER_FILTERS,
            'molecule_chembl_id': ALL,
            'pchembl_value': NUMBER_FILTERS,
            'potential_duplicate': FLAG_FILTERS,
            'published_relation': CHAR_FILTERS,
            'published_type': CHAR_FILTERS,
            'published_units': CHAR_FILTERS,
            'published_value': NUMBER_FILTERS,
            'qudt_units': CHAR_FILTERS,
            'record_id': NUMBER_FILTERS,
            'standard_flag': FLAG_FILTERS,
            'standard_relation': CHAR_FILTERS,
            'standard_type': CHAR_FILTERS,
            'standard_units': CHAR_FILTERS,
            'standard_value': NUMBER_FILTERS,
            'target_pref_name': CHAR_FILTERS,
            'target_organism': CHAR_FILTERS,
            'uo_units': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or
                                                                'canonical_smiles' in field)]

# ----------------------------------------------------------------------------------------------------------------------
