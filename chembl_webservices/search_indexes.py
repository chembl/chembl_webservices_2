__author__ = 'mnowotka'

from haystack.indexes import *
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import Assays
except ImportError:
    from chembl_core_model.models import Assays

try:
    from chembl_compatibility.models import Activities
except ImportError:
    from chembl_core_model.models import Activities

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

    def get_prefetch(self):
        return [
            Prefetch('moleculesynonyms_set'),
            Prefetch('compoundrecords_set'),
        ]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def build_queryset(self, using=None, start_date=None, end_date=None):
        return self.index_queryset(using=using).order_by(self.get_model()._meta.pk.name)

# ----------------------------------------------------------------------------------------------------------------------


class TargetDictionaryIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True, boost=1.25)
    component_synonyms = CharField(use_template=True)

    def get_model(self):
        return TargetDictionary

    def get_prefetch(self):
        return [
            Prefetch('targetcomponents_set'),
            Prefetch('targetcomponents_set__component'),
            Prefetch('targetcomponents_set__component__componentsynonyms_set'),
        ]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def build_queryset(self, using=None, start_date=None, end_date=None):
        return self.index_queryset(using=using).order_by(self.get_model()._meta.pk.name)

# ----------------------------------------------------------------------------------------------------------------------


class AssaysIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    def get_prefetch(self):
        return []

    def get_model(self):
        return Assays

# ----------------------------------------------------------------------------------------------------------------------


class DocsIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    def get_model(self):
        return Docs

    def get_prefetch(self):
        return []

    def build_queryset(self, using=None, start_date=None, end_date=None):
        return self.index_queryset(using=using).order_by(self.get_model()._meta.pk.name)

# ----------------------------------------------------------------------------------------------------------------------


class ActivityIndex(SearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    target_pref_name = CharField(use_template=True)

    def get_model(self):
        return Activities

    def get_prefetch(self):
        return [
            Prefetch('assay', queryset=Assays.objects.only('description', 'assay_id', 'target', )),
            Prefetch('assay__target', queryset=TargetDictionary.objects.only('pref_name', 'tid')),
        ]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def build_queryset(self, using=None, start_date=None, end_date=None):
        return self.index_queryset(using=using).order_by(self.get_model()._meta.pk.name)

# ----------------------------------------------------------------------------------------------------------------------
