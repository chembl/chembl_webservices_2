__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
from chembl_new_webservices.core.meta import ChemblResourceMeta
try:
    from chembl_compatibility.models import TargetComponents
except ImportError:
    from chembl_core_model.models import TargetComponents
try:
    from chembl_compatibility.models import ComponentSequences
except ImportError:
    from chembl_core_model.models import ComponentSequences
try:
    from chembl_compatibility.models import ProteinClassification
except ImportError:
    from chembl_core_model.models import ProteinClassification

#-----------------------------------------------------------------------------------------------------------------------

class ProteinClassificationResource(ChemblModelResource):

    protein_classification_id = fields.IntegerField('protein_class_id')

    class Meta(ChemblResourceMeta):
        fields = ['']
        queryset = ProteinClassification.objects.all()
        resource_name = 'protein_classification'
        collection_name = 'protein_classifications'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class TargetComponentsResource(ChemblModelResource):

    protein_classifications = fields.ToManyField(
        'chembl_new_webservices.resources.target_components.ProteinClassificationResource',
        'proteinclassification_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = ComponentSequences.objects.all()
        excludes = ['db_source', 'db_version', 'sequence_md5sum']
        resource_name = 'target_component'
        collection_name = 'target_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'accession',
            'sequence',
            'component_id',
            'component_type',
            'description',
            'organism',
            'tax_id',
        )

        filtering = {
            'accession' : ALL,
            'component_id' : ALL,
            'component_type' : ALL,
            'description' : ALL,
            'organism' : ALL,
            'tax_id': ALL,
        }

        ordering = filtering.keys()

#-----------------------------------------------------------------------------------------------------------------------
