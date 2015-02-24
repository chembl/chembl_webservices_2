__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.utils import CHAR_FILTERS, FLAG_FILTERS, NUMBER_FILTERS
from chembl_core_model.models import TargetDictionary
from chembl_core_model.models import TargetComponents

available_fields = [f.name for f in TargetDictionary._meta.fields]

#-----------------------------------------------------------------------------------------------------------------------

class TargetComponentsResource(ChemblModelResource):

    accession = fields.CharField('component__accession', null=True, blank=True)
    component_id = fields.IntegerField('component_id', null=True, blank=True)
    component_type = fields.CharField('component__component_type', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        fields = [
            'accession',
            'component_id',
            'component_type',
        ]
        filtering = {
            'accession': CHAR_FILTERS,
            'component_id': NUMBER_FILTERS,
            'component_type': CHAR_FILTERS,
        }
        queryset = TargetComponents.objects.all()
        resource_name = 'target_component'
        collection_name = 'target_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class TargetResource(ChemblModelResource):

    target_chembl_id = fields.CharField('chembl_id')
    target_type = fields.CharField('target_type_id')
    target_components = fields.ToManyField('chembl_webservices.resources.target.TargetComponentsResource',
        'targetcomponents_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = TargetDictionary.objects.all() if 'downgraded' not in available_fields else \
            TargetDictionary.objects.filter(downgraded=False)
        excludes = ['tid']
        resource_name = 'target'
        collection_name = 'targets'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name,
                                                         'target_components':'target_component'})
        detail_uri_name = 'chembl_id'
        prefetch_related = ['targetcomponents_set', 'targetcomponents_set__component']

        fields = (
            'organism',
            'pref_name',
            'species_group_flag',
            'target_chembl_id',
        )

        filtering = {
            'organism' : CHAR_FILTERS,
            'pref_name' : CHAR_FILTERS,
            'target_type': CHAR_FILTERS,
            'species_group_flag' : FLAG_FILTERS,
            'target_chembl_id' : ALL,
            'target_components': ALL_WITH_RELATIONS,
        }
        ordering = filtering.keys()

#-----------------------------------------------------------------------------------------------------------------------