__author__ = 'mnowotka'

from tastypie import fields
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_webservices.core.utils import FLAG_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.meta import ChemblResourceMeta
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import ComponentSynonyms
except ImportError:
    from chembl_core_model.models import ComponentSynonyms
try:
    from chembl_compatibility.models import TargetComponents
except ImportError:
    from chembl_core_model.models import TargetComponents
try:
    from chembl_compatibility.models import ComponentSequences
except ImportError:
    from chembl_core_model.models import ComponentSequences
try:
    from chembl_compatibility.models import ProteinClassification
except ImportError:
    from chembl_core_model.models import ProteinClassification
try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary
try:
    from chembl_compatibility.models import GoClassification
except ImportError:
    from chembl_core_model.models import GoClassification


from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

available_fields = [f.name for f in TargetDictionary._meta.fields]

# ----------------------------------------------------------------------------------------------------------------------


class ProteinClassificationResource(ChemblModelResource):

    protein_classification_id = fields.IntegerField('protein_class_id')

    class Meta(ChemblResourceMeta):
        queryset = ProteinClassification.objects.all()
        resource_name = 'protein_classification'
        collection_name = 'protein_classifications'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})

        fields = ('protein_classification_id',)

        filtering = {
            'protein_classification_id': FLAG_FILTERS,
        }

# ----------------------------------------------------------------------------------------------------------------------


class TargetDictionaryResource(ChemblModelResource):

    target_chembl_id = fields.CharField('chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = TargetDictionary.objects.all() if 'downgraded' not in available_fields else \
            TargetDictionary.objects.filter(downgraded=False)

        fields = (
            'target_chembl_id',
        )

        filtering = {
            'target_chembl_id': ALL,
        }

# ----------------------------------------------------------------------------------------------------------------------


class GoSlimResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = GoClassification.objects.all()

        fields = (
            'go_id',
        )

        filtering = {
            'go_id': ALL,
        }

# ----------------------------------------------------------------------------------------------------------------------


class TargetComponentsResource(ChemblModelResource):

    protein_classifications = fields.ToManyField(
        'chembl_webservices.resources.target_components.ProteinClassificationResource',
        'proteinclassification_set', full=True, null=True, blank=True)
    target_component_synonyms = fields.ToManyField('chembl_webservices.resources.target.TargetComponentSynonyms',
                                                   'componentsynonyms_set', full=True, null=True, blank=True)
    targets = fields.ToManyField(
        'chembl_webservices.resources.target_components.TargetDictionaryResource',
        'targetdictionary_set', full=True, null=True, blank=True)
    go_slims = fields.ToManyField(
        'chembl_webservices.resources.target_components.GoSlimResource',
        'componentgo_set', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = ComponentSequences.objects.all()
        excludes = ['db_source', 'db_version', 'sequence_md5sum']
        resource_name = 'target_component'
        collection_name = 'target_components'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name,
                                                         'target_component_synonyms': 'target_component_synonym',
                                                         'protein_classifications': 'protein_classification',
                                                         'targets': 'target'})
        prefetch_related = [
            Prefetch('proteinclassification_set',
                     queryset=ProteinClassification.objects.only('protein_class_id')),
            Prefetch('componentsynonyms_set',
                     queryset=ComponentSynonyms.objects.only('component_synonym', 'syn_type', 'compsyn_id', 'component')),
            Prefetch('targetdictionary_set',
                     queryset=TargetDictionary.objects.only('chembl_id')),
            Prefetch('componentgo_set'),
        ]

        fields = (
            'accession',
            'sequence',
            'component_id',
            'component_type',
            'description',
            'organism',
            'tax_id',
            'targets'
        )

        filtering = {
            'accession': ALL,
            'component_id': ALL,
            'component_type': ALL,
            'description': ALL,
            'organism': ALL,
            'tax_id': ALL,
            'protein_classifications': ALL_WITH_RELATIONS,
        }

        ordering = filtering.keys()

# ----------------------------------------------------------------------------------------------------------------------
