__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import TissueDictionary
except ImportError:
    from chembl_core_model.models import TissueDictionary

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class TissueResource(ChemblModelResource):

    tissue_chembl_id = fields.CharField('chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = TissueDictionary.objects.all()
        excludes = ['tissue_id']
        resource_name = 'tissue'
        collection_name = 'tissues'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        detail_uri_name = 'chembl_id'
        prefetch_related = []

        fields = (
            'uberon_id',
            'pref_name',
            'efo_id',
            'tissue_chembl_id',
            'bto_id',
            'caloha_id',
        )

        filtering = {
            'tissue_id': NUMBER_FILTERS,
            'uberon_id': ALL,
            'pref_name': CHAR_FILTERS,
            'efo_id': ALL,
            'tissue_chembl_id': ALL,
            'bto_id': ALL,
            'caloha_id': ALL,
        }

        ordering = [field for field in filtering.keys() if
                    not ('comment' in field or 'description' in field or 'canonical_smiles' in field)]

# ----------------------------------------------------------------------------------------------------------------------
