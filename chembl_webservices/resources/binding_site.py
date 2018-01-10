__author__ = 'mnowotka'

from tastypie.resources import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from django.db.models import Prefetch

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
try:
    from chembl_compatibility.models import ComponentSequences
except ImportError:
    from chembl_core_model.models import ComponentSequences

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class ComponentDomainsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = Domains.objects.all()
        resource_name = 'domain'
        collection_name = 'domains'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

        filtering = {
            'domain_description': CHAR_FILTERS,
            'domain_id': NUMBER_FILTERS,
            'domain_name': CHAR_FILTERS,
            'domain_type': CHAR_FILTERS,
            'source_domain_id': CHAR_FILTERS,
        }
        ordering = filtering.keys()

# ----------------------------------------------------------------------------------------------------------------------


class SiteComponentsResource(ChemblModelResource):

    domain = fields.ForeignKey('chembl_webservices.resources.binding_site.ComponentDomainsResource',
                               'domain', full=True, null=True, blank=True)
    component_id = fields.IntegerField('component__pk', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        excludes = ['site_residues']
        queryset = SiteComponents.objects.all()
        resource_name = 'site_component'
        collection_name = 'site_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

        filtering = {
            'component_id': NUMBER_FILTERS,
            'sitecomp_id': NUMBER_FILTERS,
            'domain': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

# ----------------------------------------------------------------------------------------------------------------------


class BindingSiteResource(ChemblModelResource):

    site_components = fields.ManyToManyField('chembl_webservices.resources.binding_site.SiteComponentsResource',
                                             'sitecomponents_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        prefetch_related = [Prefetch('sitecomponents_set'),
                            Prefetch('sitecomponents_set__domain'),
                            Prefetch('sitecomponents_set__component', queryset=ComponentSequences.objects.only('pk')),
                            ]
        queryset = BindingSites.objects.all()
        resource_name = 'binding_site'
        collection_name = 'binding_sites'
        serializer = ChEMBLApiSerializer(resource_name,
                                         {collection_name: resource_name, 'site_components': 'site_component'})
        filtering = {
            'site_id': NUMBER_FILTERS,
            'site_name': CHAR_FILTERS,
            'site_components': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

# ----------------------------------------------------------------------------------------------------------------------
