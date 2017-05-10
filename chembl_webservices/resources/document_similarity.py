__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import PaperSimilarity
except ImportError:
    from chembl_core_model.models import PaperSimilarity

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class DocumentSimilarityResource(ChemblModelResource):

    document_1_chembl_id = fields.CharField('doc_1__chembl_id', null=True, blank=True)
    document_2_chembl_id = fields.CharField('doc_2__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = PaperSimilarity.objects.all()
        detail_uri_name = 'doc_1__chembl_id'
        resource_name = 'document_similarity'
        collection_name = 'document_similarities'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = [
            Prefetch('doc_1', queryset=Docs.objects.only('chembl')),
            Prefetch('doc_2', queryset=Docs.objects.only('chembl')),
        ]

        fields = (
            'document_1_chembl_id',
            'document_2_chembl_id',
            'tid_tani',
            'mol_tani',
        )

        filtering = {
            'document_1_chembl_id': ALL,
            'document_2_chembl_id': ALL,
            'tid_tani': NUMBER_FILTERS,
            'mol_tani': NUMBER_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field
                                                                or 'canonical_smiles' in field)]

# ----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['document_similarities']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

# ----------------------------------------------------------------------------------------------------------------------

    def alter_detail_data_to_serialize(self, request, bundle):
        """
        A hook to alter detail data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for receiving a single bundle of data.
        """
        datas = bundle.data
        datas['mol_tani'] = float(datas['mol_tani'])
        datas['tid_tani'] = float(datas['tid_tani'])
        return bundle

# ----------------------------------------------------------------------------------------------------------------------
