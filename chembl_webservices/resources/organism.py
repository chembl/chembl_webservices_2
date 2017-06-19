__author__ = 'mnowotka'

from chembl_webservices.core.utils import CHAR_FILTERS
from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer

try:
    from chembl_compatibility.models import OrganismClass
except ImportError:
    from chembl_core_model.models import OrganismClass

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class OrganismResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = OrganismClass.objects.all()
        resource_name = 'organism'
        collection_name = 'organisms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        filtering = {
            'oc_id': ALL,
            'tax_id': ALL,
            'l1': CHAR_FILTERS,
            'l2': CHAR_FILTERS,
            'l3': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------
