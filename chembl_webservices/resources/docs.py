__author__ = 'mnowotka'

from tastypie import fields
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs

#-----------------------------------------------------------------------------------------------------------------------

class DocsResource(ChemblModelResource):

    document_chembl_id = fields.CharField('chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Docs.objects.all()
        excludes = ['doc_id']
        resource_name = 'document'
        collection_name = 'documents'
        detail_uri_name = 'chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'abstract',
            'authors',
            'doc_type',
            'document_chembl_id',
            'doi',
            'first_page',
            'issue',
            'journal',
            'last_page',
            'pubmed_id',
            'title',
            'volume',
            'year',
        )

        filtering = {
#            'abstract' : ALL,
            'authors' : CHAR_FILTERS,
            'doc_type' : CHAR_FILTERS,
            'document_chembl_id' : NUMBER_FILTERS,
            'doi': CHAR_FILTERS,
            'first_page': CHAR_FILTERS,
            'issue' : CHAR_FILTERS,
            'journal' : CHAR_FILTERS,
            'last_page' : CHAR_FILTERS,
            'pubmed_id' : NUMBER_FILTERS,
            'title' : CHAR_FILTERS,
            'volume' : CHAR_FILTERS,
            'year' : NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

