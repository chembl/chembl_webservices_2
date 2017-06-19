__author__ = 'mnowotka'

from django.conf.urls import url
from tastypie.utils import trailing_slash
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
try:
    from chembl_compatibility.models import ProteinFamilyClassification
except ImportError:
    from chembl_core_model.models import ProteinFamilyClassification

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class ProteinClassResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = ProteinFamilyClassification.objects.all()
        excludes = ['protein_class_desc']
        filtering = {
                     'l1': CHAR_FILTERS,
                     'l2': CHAR_FILTERS,
                     'l3': CHAR_FILTERS,
                     'l4': CHAR_FILTERS,
                     'l5': CHAR_FILTERS,
                     'l6': CHAR_FILTERS,
                     'l7': CHAR_FILTERS,
                     'l8': CHAR_FILTERS,
                     'protein_class_id': NUMBER_FILTERS
        }
        ordering = filtering.keys()
        resource_name = 'protein_class'
        collection_name = 'protein_classes'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

# ----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        """
        The standard URLs this ``Resource`` should respond to.
        """
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)/(?P<l7>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)/(?P<l7>\w[\w ]*)/(?P<l8>\w[\w ]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()),self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/search\.(?P<format>xml|json|jsonp|yaml)$" % self._meta.resource_name, self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)/(?P<l7>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<l1>\w[\w ]*)/(?P<l2>\w[\w ]*)/(?P<l3>\w[\w ]*)/(?P<l4>\w[\w ]*)/(?P<l5>\w[\w ]*)/(?P<l6>\w[\w ]*)/(?P<l7>\w[\w ]*)/(?P<l8>\w[\w ]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

# ----------------------------------------------------------------------------------------------------------------------
