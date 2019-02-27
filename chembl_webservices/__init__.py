__author__ = 'mnowotka'

try:
    __version__ = __import__('pkg_resources').get_distribution('chembl_webservices').version
except Exception as e:
    __version__ = 'development'

from django.apps import AppConfig
from django.conf import settings
from chembl_webservices.core.fields import monkeypatch_tastypie_field
from chembl_webservices.core.api import ChEMBLApi

monkeypatch_tastypie_field()
DEFAULT_API_NAME = 'chembl_ws'

try:
    api_name = settings.WS_NAME
except AttributeError:
    api_name = DEFAULT_API_NAME

api = ChEMBLApi(api_name=api_name)


class WebServicesConfig(AppConfig):
    name = 'chembl_webservices'

    def ready(self):

        from chembl_webservices.resources.activities import ActivityResource
        from chembl_webservices.resources.activities import ActivitySuppByActivityResource
        from chembl_webservices.resources.docs import DocsResource
        from chembl_webservices.resources.atc import AtcResource
        from chembl_webservices.resources.assays import AssayResource
        from chembl_webservices.resources.assays import AssayClassResource
        from chembl_webservices.resources.binding_site import BindingSiteResource
        from chembl_webservices.resources.binding_site import SiteComponentsResource
        from chembl_webservices.resources.binding_site import ComponentDomainsResource
        from chembl_webservices.resources.bio_component import BiotherapeuticComponentsResource
        from chembl_webservices.resources.cell_line import CellLineResource
        from chembl_webservices.resources.mechanism import MechanismResource
        from chembl_webservices.resources.protein_class import ProteinClassResource
        from chembl_webservices.resources.source import SourceResource
        from chembl_webservices.resources.molecule import MoleculeResource
        from chembl_webservices.resources.molecule_forms import MoleculeFormsResource
        from chembl_webservices.resources.target import TargetResource
        from chembl_webservices.resources.target_components import TargetComponentsResource
        from chembl_webservices.resources.status import StatusResource
        from chembl_webservices.resources.image import ImageResource
        from chembl_webservices.resources.substructure import SubstructureResource
        from chembl_webservices.resources.similarity import SimilarityResource
        from chembl_webservices.resources.chembl_id import ChemblIdLookupResource
        from chembl_webservices.resources.go_slim import GoSlimResource
        from chembl_webservices.resources.indication import DrugIndicationResource
        from chembl_webservices.resources.metabolism import MetabolismResource
        from chembl_webservices.resources.tissue import TissueResource
        from chembl_webservices.resources.target_relations import TargetRelationsResource
        from chembl_webservices.resources.document_similarity import DocumentSimilarityResource
        from chembl_webservices.resources.structural_alerts import CompoundStructuralAlertsResource
        from chembl_webservices.resources.document_terms import DocumentTermsResource
        from chembl_webservices.resources.compound_record import CompoundRecordsResource
        from chembl_webservices.resources.drug import DrugsResource
        from chembl_webservices.resources.target_predictions import TargetPredictionsResource
        from chembl_webservices.resources.organism import OrganismResource
        from chembl_webservices.resources.xref_source import XrefSourceResource

        api.register(StatusResource())
        api.register(DocsResource())
        api.register(ActivityResource())
        api.register(ActivitySuppByActivityResource())
        api.register(AtcResource())
        api.register(AssayResource())
        api.register(AssayClassResource())
        api.register(BindingSiteResource())
        api.register(BiotherapeuticComponentsResource())
        api.register(CellLineResource())
        api.register(MechanismResource())
        api.register(ProteinClassResource())
        api.register(SourceResource())
        api.register(MoleculeResource())
        api.register(MoleculeFormsResource())
        api.register(TargetResource())
        api.register(TargetComponentsResource())
        api.register(ImageResource())
        api.register(SubstructureResource())
        api.register(SimilarityResource())
        api.register(ChemblIdLookupResource())
        api.register(GoSlimResource())
        api.register(DrugIndicationResource())
        api.register(MetabolismResource())
        api.register(TissueResource())
        api.register(TargetRelationsResource())
        api.register(DocumentSimilarityResource())
        api.register(CompoundStructuralAlertsResource())
        api.register(DocumentTermsResource())
        api.register(CompoundRecordsResource())
        api.register(DrugsResource())
        api.register(TargetPredictionsResource())
        api.register(OrganismResource())
        api.register(XrefSourceResource())

default_app_config = 'chembl_webservices.WebServicesConfig'
