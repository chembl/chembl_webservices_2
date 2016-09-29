__author__ = 'mnowotka'

from tastypie.utils import trailing_slash
from django.conf.urls import url
from chembl_webservices import __version__
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer

try:
    from chembl_compatibility.models import Version
except ImportError:
    from chembl_core_model.models import Version

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class StatusResource(ChemblModelResource):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta(ChemblResourceMeta):
        resource_name = 'status'
        serializer = ChEMBLApiSerializer(resource_name)

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash(),),
                self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name,
                self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_list"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

#-----------------------------------------------------------------------------------------------------------------------

    def get_detail(self, request, **kwargs):
        return self.create_response(request, {'status': 'UP', 'api_version': __version__, 'chembl_db_version': Version.objects.all()[0].name})

#-----------------------------------------------------------------------------------------------------------------------

    def get_schema(self, request, **kwargs):
        return self.create_response(request, {'allowed_detail_http_methods' :
                                                  ['get'], 'allowed_list_http_methods' : ['get']})

#-----------------------------------------------------------------------------------------------------------------------

    def get_datatables(self, request, **kwargs):
        return self.create_response(request, {"columns":[{"title":"status", "data":"status", "orderable":False},
                                                         {"title":"version", "data":"version", "orderable":False}]})

#-----------------------------------------------------------------------------------------------------------------------



