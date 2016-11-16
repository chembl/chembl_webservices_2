__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
try:
    from chembl_compatibility.models import PaperSimilarityVw
except ImportError:
    from chembl_core_model.models import PaperSimilarityVw

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class DocumentSimilarityResource(ChemblModelResource):

    document_1_chembl_id = fields.CharField('doc_1__chembl__chembl_id', null=True, blank=True)
    document_2_chembl_id = fields.CharField('doc_2__chembl__chembl_id', null=True, blank=True)


    class Meta(ChemblResourceMeta):
        queryset = PaperSimilarityVw.objects.all()
        detail_uri_name = 'doc_1__chembl_id'
        resource_name = 'document_similarity'
        collection_name = 'document_similarities'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['doc_1', 'doc_1__chembl','doc_2', 'doc_2__chembl']
        fields = (
            'document_1_chembl_id',
            'document_2_chembl_id',
            'tid_tani',
            'mol_tani',
        )

        filtering = {
            'document_1_chembl_id' : ALL,
            'document_2_chembl_id': ALL,
            'tid_tani': NUMBER_FILTERS,
            'mol_tani': NUMBER_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or 'canonical_smiles' in field) ]

#-----------------------------------------------------------------------------------------------------------------------