__author__ = 'mnowotka'

from tastypie.resources import ALL
from tastypie import fields
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import BioComponentSequences
except ImportError:
    from chembl_core_model.models import BioComponentSequences

try:
    from chembl_compatibility.models import Biotherapeutics
except ImportError:
    from chembl_core_model.models import Biotherapeutics

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

#-----------------------------------------------------------------------------------------------------------------------

class BioComponentsSequencesResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = BioComponentSequences.objects.all()
        excludes = ['sequence_md5sum']
        resource_name = 'biocomponent'
        collection_name = 'biocomponents'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'component_id',
            'component_type',
            'description',
            'sequence',
            'tax_id',
            'organism',
        )

        filtering = {
            'component_id' : NUMBER_FILTERS,
            'component_type' : CHAR_FILTERS,
#            'description' : ALL,
            'organism' : CHAR_FILTERS,
            'tax_id' : NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

class BiotherapeuticComponentsResource(ChemblModelResource):

    biocomponents = fields.ToManyField('chembl_webservices.resources.bio_component.BioComponentsSequencesResource',
        'bio_component_sequences', full=True, null=True, blank=True)
    molecule_chembl_id = fields.CharField('molecule__chembl__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = Biotherapeutics.objects.all()
        resource_name = 'biotherapeutic'
        collection_name = 'biotherapeutics'
        detail_uri_name = 'molecule__chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name, 'biocomponents':'biocomponent',})
        prefetch_related = ['bio_component_sequences', 'molecule__chembl']
        fields = (
            'molecule_chembl_id',
            'description',
            'helm_notation',
            'biocomponents',
        )

        filtering = {
            'molecule_chembl_id' : CHAR_FILTERS,
            'helm_notation' : CHAR_FILTERS,
            'description': FLAG_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------