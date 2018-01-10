__author__ = 'mnowotka'

from chembl_webservices.core.utils import CHAR_FILTERS
from tastypie import fields
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer

try:
    from chembl_compatibility.models import XrefSource
except ImportError:
    from chembl_core_model.models import XrefSource

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class XrefSourceResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = XrefSource.objects.all()
        excludes = []
        resource_name = 'xref_source'
        collection_name = 'xref_sources'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

        filtering = {
            'xref_src_db': CHAR_FILTERS,
            'xref_src_description': CHAR_FILTERS,
            'xref_src_url': CHAR_FILTERS,
            'xref_id_url': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------
