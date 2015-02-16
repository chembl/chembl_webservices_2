__author__ = 'mnowotka'

from chembl_new_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.meta import ChemblResourceMeta
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import Source
except ImportError:
    from chembl_core_model.models import Source

#-----------------------------------------------------------------------------------------------------------------------

class SourceResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = Source.objects.all()
        resource_name = 'source'
        collection_name = 'sources'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        filtering = {
            'src_description' : CHAR_FILTERS,
            'src_id' : NUMBER_FILTERS,
            'src_short_name': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------