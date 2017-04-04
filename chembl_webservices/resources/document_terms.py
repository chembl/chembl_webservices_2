__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import Doc2Term
except ImportError:
    from chembl_core_model.models import Doc2Term
try:
    from chembl_compatibility.models import DocumentTerms
except ImportError:
    from chembl_core_model.models import DocumentTerms
try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class DocumentTermsResource(ChemblModelResource):

    term_text = fields.CharField('term__term', null=True, blank=True)
    document_chembl_id = fields.CharField('doc__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Doc2Term.objects.all()
        resource_name = 'document_term'
        collection_name = 'document_terms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = [
            Prefetch('term', queryset=DocumentTerms.objects.only('term')),
            Prefetch('doc', queryset=Docs.objects.only('chembl')),
        ]
        fields = (
            'score',
            'term_text',
            'document_chembl_id',
        )
        filtering = {
            'term_text': CHAR_FILTERS,
            'score': NUMBER_FILTERS,
            'document_chembl_id': ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or
                                                                'canonical_smiles' in field)]

# ----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['document_terms']
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
        datas['score'] = round(float(datas['score']), 6)
        return bundle

# ----------------------------------------------------------------------------------------------------------------------
