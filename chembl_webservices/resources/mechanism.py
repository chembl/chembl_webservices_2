__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_new_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
from chembl_new_webservices.core.meta import ChemblResourceMeta
try:
    from chembl_compatibility.models import DrugMechanism
except ImportError:
    from chembl_core_model.models import DrugMechanism

#-----------------------------------------------------------------------------------------------------------------------

class MechanismResource(ChemblModelResource):

    record_id = fields.IntegerField('record_id', null=True, blank=True)
    molecule_chembl_id = fields.CharField('molecule__chembl_id', null=True, blank=True)
    target_chembl_id = fields.CharField('target__chembl_id', null=True, blank=True)
    site_id = fields.IntegerField('site_id', null=True, blank=True)
    action_type = fields.CharField('action_type_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = DrugMechanism.objects.all()
        resource_name = 'mechanism'
        collection_name = 'mechanisms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'action_type',
            'binding_site_comment',
            'direct_interaction',
            'disease_efficacy',
            'mec_id',
            'mechanism_comment',
            'mechanism_of_action',
            'molecular_mechanism',
            'molecule_chembl_id',
            'record_id',
            'selectivity_comment',
            'site_id',
            'target_chembl_id',
        )

        filtering = {
            'action_type' : CHAR_FILTERS,
#            'binding_site_comment' : ALL,
            'direct_interaction' : FLAG_FILTERS,
            'disease_efficacy' : FLAG_FILTERS,
            'mec_id' : NUMBER_FILTERS,
#            'mechanism_comment' : ALL,
            'mechanism_of_action' : CHAR_FILTERS,
            'molecular_mechanism' : FLAG_FILTERS,
            'molecule_chembl_id' : ALL,
            'record_id' : NUMBER_FILTERS,
#            'selectivity_comment' : ALL,
            'site_id' : NUMBER_FILTERS,
            'target_chembl_id' : ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------