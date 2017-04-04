__author__ = 'mnowotka'

from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import TargetPredictions
except ImportError:
    from chembl_core_model.models import TargetPredictions
try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class TargetPredictionsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = TargetPredictions.objects.all()
        resource_name = 'target_prediction'
        collection_name = 'target_predictions'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = []
        filtering = {
            'pred_id': ALL,
            'molecule_chembl_id': ALL,
            'target_chembl_id': ALL,
            'target_accession': CHAR_FILTERS,
            'probability': NUMBER_FILTERS,
            'in_training': FLAG_FILTERS,
            'value': NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------
