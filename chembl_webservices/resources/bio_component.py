__author__ = 'mnowotka'

from tastypie.resources import ALL
from chembl_new_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.meta import ChemblResourceMeta
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import BioComponentSequences
except ImportError:
    from chembl_core_model.models import BioComponentSequences

#-----------------------------------------------------------------------------------------------------------------------

class BiotherapeuticComponentsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = BioComponentSequences.objects.all()
        excludes = ['sequence_md5sum']
        resource_name = 'biocomponent'
        collection_name = 'biocomponents'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'component_id',
            'component_type',
            'description',
            'sequence',
            'tax_id',
            'organism',
        )

        filtering = {
            'component_id' : NUMBER_FILTERS,
            'component_type' : CHAR_FILTERS,
#            'description' : ALL,
            'organism' : CHAR_FILTERS,
            'tax_id' : NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------