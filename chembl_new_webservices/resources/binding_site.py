__author__ = 'mnowotka'

from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
from chembl_new_webservices.core.meta import ChemblResourceMeta
from chembl_new_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
try:
    from chembl_compatibility.models import BindingSites
except ImportError:
    from chembl_core_model.models import BindingSites
try:
    from chembl_compatibility.models import SiteComponents
except ImportError:
    from chembl_core_model.models import SiteComponents
try:
    from chembl_compatibility.models import Domains
except ImportError:
    from chembl_core_model.models import Domains

#-----------------------------------------------------------------------------------------------------------------------

class ComponentDomainsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = Domains.objects.all()
        resource_name = 'domain'
        collection_name = 'domains'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class SiteComponentsResource(ChemblModelResource):

    domain = fields.ForeignKey('chembl_new_webservices.resources.binding_site.ComponentDomainsResource',
        'domain', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = SiteComponents.objects.all()
        resource_name = 'site_component'
        collection_name = 'site_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class BindingSiteResource(ChemblModelResource):

    site_components = fields.ManyToManyField('chembl_new_webservices.resources.binding_site.SiteComponentsResource',
        'sitecomponents_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = BindingSites.objects.all()
        resource_name = 'binding_site'
        collection_name = 'binding_sites'
        serializer = ChEMBLApiSerializer(resource_name,
            {collection_name : resource_name, 'site_components':'site_component'})
        filtering = {
            'site_id' : NUMBER_FILTERS,
            'site_name' : CHAR_FILTERS,
        }
        ordering = filtering.keys()

#-----------------------------------------------------------------------------------------------------------------------