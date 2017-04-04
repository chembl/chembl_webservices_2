__author__ = 'mnowotka'

from haystack.indexes import *
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import Assays
except ImportError:
    from chembl_core_model.models import Assays

try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs

try:
    from chembl_compatibility.models import CompoundRecords
except ImportError:
    from chembl_core_model.models import CompoundRecords

try:
    from chembl_compatibility.models import ComponentSequences
except ImportError:
    from chembl_core_model.models import ComponentSequences

try:
    from chembl_compatibility.models import ComponentSynonyms
except ImportError:
    from chembl_core_model.models import ComponentSynonyms

try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

try:
    from chembl_compatibility.models import MoleculeSynonyms
except ImportError:
    from chembl_core_model.models import MoleculeSynonyms

try:
    from chembl_compatibility.models import TargetComponents
except ImportError:
    from chembl_core_model.models import TargetComponents

try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary

# ----------------------------------------------------------------------------------------------------------------------


class MoleculeDictionaryIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True, boost=1.25)
    synonyms = CharField(use_template=True)
    compound_keys = CharField(use_template=True, boost=0.8)
    record_names = CharField(use_template=True, boost=0.7)

    def get_model(self):
        return MoleculeDictionary

    def index_queryset(self, using=None):
        return self.get_model().objects.prefetch_related(
            Prefetch('moleculesynonyms_set'),
            Prefetch('compoundrecords_set'),
        )

# ----------------------------------------------------------------------------------------------------------------------


class TargetDictionaryIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True, boost=1.25)
    component_synonyms = CharField(use_template=True)

    def get_model(self):
        return TargetDictionary

    def index_queryset(self, using=None):
        return self.get_model().objects.prefetch_related(
            Prefetch('targetcomponents_set'),
            Prefetch('targetcomponents_set__component'),
            Prefetch('targetcomponents_set__component__componentsynonyms_set'),
        )

# ----------------------------------------------------------------------------------------------------------------------


class AssaysIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    def get_model(self):
        return Assays

# ----------------------------------------------------------------------------------------------------------------------


class DocsIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    def get_model(self):
        return Docs

# ----------------------------------------------------------------------------------------------------------------------
