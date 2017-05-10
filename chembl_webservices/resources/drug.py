__author__ = 'mnowotka'

from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer

try:
    from chembl_compatibility.models import MoleculeBrowseDrugs
except ImportError:
    from chembl_core_model.models import MoleculeBrowseDrugs

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class DrugsResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = MoleculeBrowseDrugs.objects.all()
        excludes = ['drug_type_text', 'rule_of_five_text', 'first_in_class_text', 'chirality_text', 'prodrug_text',
                    'oral_text', 'parenteral_text', 'topical_text', 'black_box_text', 'availability_type_text',
                    'parent_molregno', 'atc_code']
        resource_name = 'drug'
        collection_name = 'drugs'
        detail_uri_name = 'chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        prefetch_related = []
        filtering = {
            'applicants': CHAR_FILTERS,
            'atc_code': CHAR_FILTERS,
            'atc_code_description': CHAR_FILTERS,
            'availability_type': NUMBER_FILTERS,
            'black_box': FLAG_FILTERS,
            'chirality': NUMBER_FILTERS,
            'development_phase': NUMBER_FILTERS,
            'drug_type': NUMBER_FILTERS,
            'first_approval': NUMBER_FILTERS,
            'first_in_class': FLAG_FILTERS,
            'indication_class': CHAR_FILTERS,
            'molecule_chembl_id': ALL,
            'ob_patent': CHAR_FILTERS,
            'oral': FLAG_FILTERS,
            'parenteral': FLAG_FILTERS,
            'prodrug': FLAG_FILTERS,
            'research_codes': CHAR_FILTERS,
            'rule_of_five': FLAG_FILTERS,
            'sc_patent': CHAR_FILTERS,
            'synonyms': CHAR_FILTERS,
            'topical': FLAG_FILTERS,
            'usan_stem': CHAR_FILTERS,
            'usan_stem_definition': CHAR_FILTERS,
            'usan_stem_substem': CHAR_FILTERS,
            'usan_year': NUMBER_FILTERS,
            'withdrawn_country': CHAR_FILTERS,
            'withdrawn_reason': CHAR_FILTERS,
            'withdrawn_year': NUMBER_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field)]

# ----------------------------------------------------------------------------------------------------------------------


    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['drugs']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

# ----------------------------------------------------------------------------------------------------------------------


    def alter_detail_data_to_serialize(self, request, bundle):

        data = bundle.data
        data['applicants'] = map(lambda x: x.strip(), data['applicants'].split(';')) if data['applicants'] else None
        data['research_codes'] = map(lambda x: x.strip(), data['research_codes'].split(';')) if data['research_codes'] else None
        data['synonyms'] = map(lambda x: x.strip(), data['synonyms'].split(';')) if data['synonyms'] else None
        data['atc_code_description'] = [{'code': x.split()[0], 'description': x.split('[')[1][:-1]} for x in
                                        map(lambda x: x.strip(), data['atc_code_description'].split(';'))] \
            if data['atc_code_description'] else None
        data['atc_classification'] = data.pop('atc_code_description')
        return bundle


# ----------------------------------------------------------------------------------------------------------------------
