__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
try:
    from chembl_compatibility.models import Doc2Term
except ImportError:
    from chembl_core_model.models import Doc2Term

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class DocumentTermsResource(ChemblModelResource):

    term_text = fields.CharField('term__term', null=True, blank=True)
    document_chembl_id = fields.CharField('doc__chembl__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Doc2Term.objects.all()
        resource_name = 'document_term'
        collection_name = 'document_terms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['term', 'doc', 'doc__chembl']
        fields = (
            'score',
            'term_text',
            'document_chembl_id',
        )
        filtering = {
            'term_text' : CHAR_FILTERS,
            'score' : NUMBER_FILTERS,
            'document_chembl_id' : ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or 'canonical_smiles' in field) ]

#-----------------------------------------------------------------------------------------------------------------------