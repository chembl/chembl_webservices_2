__author__ = 'mnowotka'

from tastypie import fields
from django.conf.urls import url
from tastypie.utils import trailing_slash
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class DocsResource(ChemblModelResource):

    document_chembl_id = fields.CharField('chembl__chembl_id', null=True, blank=True)
    score = fields.FloatField('score', use_in='search', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Docs.objects.all()
        excludes = ['doc_id']
        resource_name = 'document'
        collection_name = 'documents'
        detail_uri_name = 'chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['chembl']

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
            'abstract' : FLAG_FILTERS,
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

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/search\.(?P<format>xml|json|jsonp|yaml)$" % self._meta.resource_name, self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

