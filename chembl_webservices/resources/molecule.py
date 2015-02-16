__author__ = 'mnowotka'

from tastypie import fields
from tastypie.utils import trailing_slash
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from django.conf.urls import url
from chembl_new_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
from chembl_new_webservices.core.meta import ChemblResourceMeta
from django.core.exceptions import ObjectDoesNotExist
from tastypie.exceptions import Unauthorized
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from tastypie.utils import dict_strip_unicode_keys
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary
try:
    from chembl_compatibility.models import CompoundProperties
except ImportError:
    from chembl_core_model.models import CompoundProperties
try:
    from chembl_compatibility.models import CompoundStructures
except ImportError:
    from chembl_core_model.models import CompoundStructures
try:
    from chembl_compatibility.models import MoleculeSynonyms
except ImportError:
    from chembl_core_model.models import MoleculeSynonyms
try:
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeHierarchy

available_fields = [f.name for f in MoleculeDictionary._meta.fields]

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeHierarchyResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('molecule__chembl_id')
    parent_chembl_id = fields.CharField('parent_molecule__chembl_id', null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = MoleculeHierarchy.objects.all()
        resource_name = 'molecule_hierarchy'
        filtering = {
            'molecule_chembl_id' : ALL,
            'parent_chembl_id' : ALL,
        }
        ordering = filtering.keys()

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeSynonymsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = MoleculeSynonyms.objects.all()
        excludes = ['molsyn_id']
        resource_name = 'synonym'
        collection_name = 'molecule_synonyms'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeStructuresResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = CompoundStructures.objects.all()
        excludes = ['molfile']
        resource_name = 'molecule_structures'
        collection_name = 'molecule_structures'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'standard_inchi',
            'standard_inchi_key',
            'canonical_smiles',
        )

        filtering = {
            'canonical_smiles' : CHAR_FILTERS,
            'standard_inchi_key' : CHAR_FILTERS,
        }

#-----------------------------------------------------------------------------------------------------------------------

class MoleculePropertiesResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = CompoundProperties.objects.all()
        resource_name = 'molecule_properties'
        collection_name = 'molecule_properties'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'acd_logd',
            'acd_logp',
            'acd_most_apka',
            'acd_most_bpka',
            'alogp',
            'aromatic_rings',
            'full_molformula',
            'full_mwt',
            'hba',
            'hbd',
            'heavy_atoms',
            'med_chem_friendly',
            'molecular_species',
            'mw_freebase',
            'mw_monoisotopic',
            'num_alerts',
            'num_ro5_violations',
            'psa',
            'qed_weighted',
            'ro3_pass',
            'rtb',
        )

        filtering = {
            'acd_logd' : NUMBER_FILTERS,
            'acd_logp' : NUMBER_FILTERS,
            'acd_most_apka' : NUMBER_FILTERS,
            'acd_most_bpka' : NUMBER_FILTERS,
            'alogp' : NUMBER_FILTERS,
            'aromatic_rings' : NUMBER_FILTERS,
            'full_molformula' : CHAR_FILTERS,
            'full_mwt' : NUMBER_FILTERS,
            'hba' : NUMBER_FILTERS,
            'hbd' : NUMBER_FILTERS,
            'heavy_atoms' : NUMBER_FILTERS,
            'med_chem_friendly' : CHAR_FILTERS,
            'molecular_species' : CHAR_FILTERS,
            'mw_freebase' : NUMBER_FILTERS,
            'mw_monoisotopic' : NUMBER_FILTERS,
            'num_alerts' : NUMBER_FILTERS,
            'num_ro5_violations' : NUMBER_FILTERS,
            'psa' : NUMBER_FILTERS,
            'qed_weighted' : NUMBER_FILTERS,
            'ro3_pass' : CHAR_FILTERS,
            'rtb' : NUMBER_FILTERS,
        }
        ordering = filtering.keys()

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('chembl_id')
    molecule_properties = fields.ForeignKey('chembl_new_webservices.resources.molecule.MoleculePropertiesResource',
        'compoundproperties', full=True, null=True, blank=True)
    molecule_hierarchy = fields.ForeignKey('chembl_new_webservices.resources.molecule.MoleculeHierarchyResource',
        'moleculehierarchy', full=True, null=True, blank=True)
    molecule_structures = fields.ForeignKey('chembl_new_webservices.resources.molecule.MoleculeStructuresResource',
        'compoundstructures', full=True, null=True, blank=True)
    molecule_synonyms = fields.ToManyField('chembl_new_webservices.resources.molecule.MoleculeSynonymsResource',
        'moleculesynonyms_set', full=True, null=True, blank=True)
    biocomponents = fields.ToManyField('chembl_new_webservices.resources.bio_component.BiotherapeuticComponentsResource',
        'biotherapeutics__bio_component_sequences', full=True, null=True, blank=True)
    helm_notation = fields.CharField('biotherapeutics__helm_notation', null=True, blank=True)
    biotherapeutic = fields.BooleanField('biotherapeutics', null=True, blank=True)
    atc_classifications = fields.ToManyField('chembl_new_webservices.resources.atc.AtcResource',
        'atcclassification_set', full=False, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = MoleculeDictionary.objects.all() if 'downgraded' not in available_fields else \
                    MoleculeDictionary.objects.exclude(downgraded=True)
        excludes = ['molregno']
        resource_name = 'molecule'
        collection_name = 'molecules'
        serializer = ChEMBLApiSerializer(resource_name,
            {collection_name : resource_name, 'biocomponents':'biocomponent', 'molecule_synonyms': 'synonym', 'atc_classifications': 'level5'})
        detail_uri_name = 'chembl_id'

        fields = (
            'atc_classifications',
            'availability_type',
            'biotherapeutic',
            'black_box_warning',
            'chebi_par_id',
            'chirality',
            'dosed_ingredient',
            'first_approval',
            'first_in_class',
            'helm_notation',
            'indication_class',
            'inorganic_flag',
            'max_phase',
            'molecule_chembl_id',
            'molecule_hierarchy',
            'molecule_properties',
            'molecule_structures',
            'molecule_type',
            'natural_product',
            'oral',
            'parenteral',
            'polymer_flag',
            'pref_name',
            'prodrug',
            'structure_type',
            'therapeutic_flag',
            'topical',
            'usan_stem',
            'usan_stem_definition',
            'usan_substem',
            'usan_year',
        )

        filtering = {
            'availability_type' : CHAR_FILTERS,
            'biotherapeutic' : FLAG_FILTERS,
            'black_box_warning' : FLAG_FILTERS,
            'chebi_par_id' : NUMBER_FILTERS,
            'chirality' : NUMBER_FILTERS,
            'dosed_ingredient' : FLAG_FILTERS,
            'first_approval' : NUMBER_FILTERS,
            'first_in_class' : FLAG_FILTERS,
            'indication_class' : CHAR_FILTERS,
            'inorganic_flag' : FLAG_FILTERS,
            'helm_notation': CHAR_FILTERS,
            'max_phase' : NUMBER_FILTERS,
            'molecule_chembl_id' : ALL,
            'atc_classifications' : ALL_WITH_RELATIONS,
            'molecule_hierarchy': ALL_WITH_RELATIONS,
            'molecule_properties' : ALL_WITH_RELATIONS,
            'molecule_structures': ALL_WITH_RELATIONS,
            'molecule_type' : CHAR_FILTERS,
            'natural_product' : FLAG_FILTERS,
            'oral' : FLAG_FILTERS,
            'parenteral' : FLAG_FILTERS,
            'polymer_flag' : FLAG_FILTERS,
            'pref_name' : CHAR_FILTERS,
            'prodrug' : FLAG_FILTERS,
            'structure_type' : CHAR_FILTERS,
            'therapeutic_flag' : FLAG_FILTERS,
            'topical' : FLAG_FILTERS,
            'usan_stem' : CHAR_FILTERS,
            'usan_stem_definition' : CHAR_FILTERS,
            'usan_substem' : CHAR_FILTERS,
            'usan_year' : NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):

        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<chembl_id_list>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*(;[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<chembl_id_list>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*(;[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<molecule_structures__standard_inchi_key_list>[A-Z]{14}-[A-Z]{10}-[A-Z](;[A-Z]{14}-[A-Z]{10}-[A-Z])*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<molecule_structures__standard_inchi_key_list>[A-Z]{14}-[A-Z]{10}-[A-Z](;[A-Z]{14}-[A-Z]{10}-[A-Z])*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<molecule_structures__canonical_smiles_list>[^jx]+(;[^jx]+)*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/set/(?P<molecule_structures__canonical_smiles_list>[^jx]+(;[^jx]+)*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule_structures__standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule_structures__standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule_structures__canonical_smiles>[^jx]+)\.(?P<format>json|xml)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule_structures__canonical_smiles>[^jx]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

#-----------------------------------------------------------------------------------------------------------------------

    def get_multiple(self, request, **kwargs):
        """
        Returns a serialized list of resources based on the identifiers
        from the URL.

        Calls ``obj_get`` to fetch only the objects requested. This method
        only responds to HTTP GET.

        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        detail_uri_name = None
        obj_identifiers = None

        for key, value in kwargs.items():
            if key.endswith('_list'):
                detail_uri_name = key.split('_list')[0]
                obj_identifiers = value.split(';')
                break

        objects = []
        not_found = []
        base_bundle = self.build_bundle(request=request)

        for identifier in obj_identifiers:
            try:
                obj = self.obj_get(bundle=base_bundle, **{detail_uri_name: identifier})
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle, for_list=True)
                objects.append(bundle)
            except (ObjectDoesNotExist, Unauthorized):
                not_found.append(identifier)

        object_list = {
            self._meta.collection_name: objects,
        }

        if len(not_found):
            object_list['not_found'] = not_found

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

#-----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        bundles = data['molecules']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

#-----------------------------------------------------------------------------------------------------------------------

    def alter_detail_data_to_serialize(self, request, data):
        atc = data.data['atc_classifications']
        for idx, item in enumerate(atc):
            atc[idx] = item.split('/')[-1]
        return data

#-----------------------------------------------------------------------------------------------------------------------
