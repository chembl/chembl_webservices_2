__author__ = 'mnowotka'

from chembl_new_webservices.resources.activities import ActivityResource
from chembl_new_webservices.resources.assays import AssayResource
from chembl_new_webservices.resources.atc import AtcResource
from chembl_new_webservices.resources.binding_site import BindingSiteResource
from chembl_new_webservices.resources.bio_component import BiotherapeuticComponentsResource
from chembl_new_webservices.resources.cell_line import CellLineResource
from chembl_new_webservices.resources.docs import DocsResource
from chembl_new_webservices.resources.image import ImageResource
from chembl_new_webservices.resources.mechanism import MechanismResource
from chembl_new_webservices.resources.molecule import MoleculeResource
from chembl_new_webservices.resources.molecule_forms import MoleculeFormsResource
from chembl_new_webservices.resources.protein_class import ProteinClassResource
from chembl_new_webservices.resources.similarity import SimilarityResource
from chembl_new_webservices.resources.source import SourceResource
from chembl_new_webservices.resources.status import StatusResource
from chembl_new_webservices.resources.substructure import SubstructureResource
from chembl_new_webservices.resources.target import TargetResource
from chembl_new_webservices.resources.target_components import TargetComponentsResource

__all__ = [
    'ActivityResource',
    'AssayResource',
    'AtcResource',
    'BindingSiteResource',
    'BiotherapeuticComponentsResource',
    'CellLineResource',
    'DocsResource',
    'ImageResource',
    'MechanismResource',
    'MoleculeResource',
    'MoleculeFormsResource',
    'ProteinClassResource',
    'SimilarityResource',
    'SourceResource',
    'StatusResource',
    'SubstructureResource',
    'TargetResource',
    'TargetComponentsResource',
]
