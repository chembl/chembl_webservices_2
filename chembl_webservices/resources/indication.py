__author__ = 'mnowotka'

from tastypie import fields
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from django.db.models import Prefetch
try:
    from chembl_compatibility.models import DrugIndication
    from chembl_compatibility.models import IndicationRefs
except ImportError:
    from chembl_core_model.models import DrugIndication
    from chembl_core_model.models import IndicationRefs
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class IndicationRefsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = IndicationRefs.objects.all()
        excludes = []
        resource_name = 'indication_ref'
        collection_name = 'indication_refs'
        detail_uri_name = 'indref_id'
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


class DrugIndicationResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('molecule__chembl_id', null=True, blank=True)
    indication_refs = fields.ToManyField('chembl_webservices.resources.indication.IndicationRefsResource',
                                         'indicationrefs_set', full=True, null=True, blank=True)
    parent_molecule_chembl_id = fields.CharField('molecule__moleculehierarchy__parent_molecule__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = DrugIndication.objects.all()
        excludes = []
        resource_name = 'drug_indication'
        collection_name = 'drug_indications'
        detail_uri_name = 'drugind_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = [
            Prefetch('molecule', queryset=MoleculeDictionary.objects.only('chembl')),
            'indicationrefs_set',
            Prefetch('molecule__moleculehierarchy'),
            Prefetch('molecule__moleculehierarchy__parent_molecule',
                     queryset=MoleculeDictionary.objects.only('chembl')),
        ]

        fields = (
            'drugind_id',
            'molecule_chembl_id',
            'max_phase_for_ind',
            'mesh_id',
            'mesh_heading',
            'efo_id',
            'efo_term',
            'indication_refs',
            'parent_molecule_chembl_id',
        )

        filtering = {
            'drugind_id': NUMBER_FILTERS,
            'molecule_chembl_id': ALL,
            'parent_molecule_chembl_id': ALL,
            'max_phase_for_ind': NUMBER_FILTERS,
            'mesh_id': CHAR_FILTERS,
            'mesh_heading': CHAR_FILTERS,
            'efo_id': CHAR_FILTERS,
            'efo_term': CHAR_FILTERS,
            'indication_refs': ALL_WITH_RELATIONS,
        }
        
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------


