__author__ = 'mnowotka'

from haystack.indexes import *
from haystack import site

try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

try:
    from chembl_compatibility.models import MoleculeSynonyms
except ImportError:
    from chembl_core_model.models import MoleculeSynonyms

try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary

try:
    from chembl_compatibility.models import ComponentSynonyms
except ImportError:
    from chembl_core_model.models import ComponentSynonyms

try:
    from chembl_compatibility.models import Assays
except ImportError:
    from chembl_core_model.models import Assays

try:
    from chembl_compatibility.models import Docs
except ImportError:
    from chembl_core_model.models import Docs

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeDictionaryIndex(SearchIndex):
    text = CharField(document=True, use_template=True)

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeSynonymsIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    syn_type = CharField(model_attr='syn_type', null=True)

#-----------------------------------------------------------------------------------------------------------------------

class TargetDictionaryIndex(SearchIndex):
    text = CharField(document=True, use_template=True)

#-----------------------------------------------------------------------------------------------------------------------

class ComponentSynonymsIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    syn_type = CharField(model_attr='syn_type', null=True)

#-----------------------------------------------------------------------------------------------------------------------

class AssaysIndex(SearchIndex):
    text = CharField(document=True, use_template=True)

#-----------------------------------------------------------------------------------------------------------------------

class DocsIndex(SearchIndex):
    text = CharField(document=True, use_template=True)

#-----------------------------------------------------------------------------------------------------------------------

site.register(MoleculeDictionary, MoleculeDictionaryIndex)
site.register(MoleculeSynonyms, MoleculeSynonymsIndex)
site.register(TargetDictionary, TargetDictionaryIndex)
site.register(ComponentSynonyms, ComponentSynonymsIndex)
site.register(Assays, AssaysIndex)
site.register(Docs, DocsIndex)