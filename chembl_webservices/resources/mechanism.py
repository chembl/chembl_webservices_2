__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import ActionType
except ImportError:
    from chembl_core_model.models import ActionType
try:
    from chembl_compatibility.models import BindingSites
except ImportError:
    from chembl_core_model.models import BindingSites
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import CompoundRecords
except ImportError:
    from chembl_core_model.models import CompoundRecords
try:
    from chembl_compatibility.models import DrugMechanism
except ImportError:
    from chembl_core_model.models import DrugMechanism
try:
    from chembl_compatibility.models import MechanismRefs
except ImportError:
    from chembl_core_model.models import MechanismRefs
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary
try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class MechanismRefsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = MechanismRefs.objects.all()
        excludes = []
        resource_name = 'mechanism_ref'
        collection_name = 'mechanism_refs'
        detail_uri_name = 'mecref_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = []

        fields = (
            'ref_type',
            'ref_id',
            'ref_url',
        )

        filtering = {
            'ref_type': CHAR_FILTERS,
            'ref_id': CHAR_FILTERS,
            'ref_url': CHAR_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------


class MechanismResource(ChemblModelResource):

    record_id = fields.IntegerField('record_id', null=True, blank=True)
    molecule_chembl_id = fields.CharField('molecule__chembl_id', null=True, blank=True)
    max_phase = fields.IntegerField('molecule__max_phase', null=True, blank=True)
    target_chembl_id = fields.CharField('target__chembl_id', null=True, blank=True)
    site_id = fields.IntegerField('site_id', null=True, blank=True)
    action_type = fields.CharField('action_type_id', null=True, blank=True)
    mechanism_refs = fields.ToManyField('chembl_webservices.resources.mechanism.MechanismRefsResource',
                                        'mechanismrefs_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = DrugMechanism.objects.all()
        resource_name = 'mechanism'
        collection_name = 'mechanisms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = [
            Prefetch('molecule', queryset=MoleculeDictionary.objects.only('chembl', 'max_phase')),
            Prefetch('target', queryset=TargetDictionary.objects.only('chembl')),
            Prefetch('mechanismrefs_set')
        ]

        fields = (
            'action_type',
            'binding_site_comment',
            'direct_interaction',
            'disease_efficacy',
            'max_phase',
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
            'action_type': CHAR_FILTERS,
#            'binding_site_comment': ALL,
            'direct_interaction': FLAG_FILTERS,
            'disease_efficacy': FLAG_FILTERS,
            'max_phase': NUMBER_FILTERS,
            'mec_id': NUMBER_FILTERS,
#            'mechanism_comment': ALL,
            'mechanism_of_action': CHAR_FILTERS,
            'molecular_mechanism': FLAG_FILTERS,
            'molecule_chembl_id': ALL,
            'record_id' : NUMBER_FILTERS,
#            'selectivity_comment': ALL,
            'site_id': NUMBER_FILTERS,
            'target_chembl_id': ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------
