__author__ = 'mnowotka'

from tastypie import fields
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.resources.molecule import MoleculeResource
from chembl_webservices.resources.assays import AssayResource
from chembl_webservices.resources.target import TargetResource
from chembl_webservices.resources.docs import DocsResource
from chembl_webservices.resources.cell_line import CellLineResource
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup

molecule = MoleculeResource()
assay = AssayResource()
target = TargetResource()
document = DocsResource()
cell = CellLineResource()

#-----------------------------------------------------------------------------------------------------------------------

class ChemblIdLookupResource(ChemblModelResource):

    resource_url = fields.CharField()

    class Meta(ChemblResourceMeta):
        queryset = ChemblIdLookup.objects.all()
        resource_name = 'chembl_id_lookup'
        collection_name = 'chembl_id_lookups'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        fields = (
            'chembl_id',
            'entity_type',
            'status',
        )
        filtering = {
            'chembl_id' : CHAR_FILTERS,
            'entity_type': CHAR_FILTERS,
            'status': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['chembl_id_lookups']
        for idx, bundle in enumerate(bundles):
            bundles[idx] = self.alter_detail_data_to_serialize(request, bundle)
        return data

#-----------------------------------------------------------------------------------------------------------------------

    def alter_detail_data_to_serialize(self, request, bundle):
        """
        A hook to alter detail data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for receiving a single bundle of data.
        """
        datas = bundle.data
        detail_name = 'api_dispatch_detail'
        if datas['entity_type'] == 'COMPOUND':
            datas['resource_url'] = molecule._build_reverse_url(detail_name,
                kwargs=molecule.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'ASSAY':
            datas['resource_url'] = assay._build_reverse_url(detail_name,
                kwargs=assay.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'TARGET':
            datas['resource_url'] = target._build_reverse_url(detail_name,
                kwargs=target.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'DOCUMENT':
            datas['resource_url'] = document._build_reverse_url(detail_name,
                kwargs=document.resource_uri_kwargs(bundle))
        elif datas['entity_type'] == 'CELL':
            kw = cell.resource_uri_kwargs(bundle)
            kw['cell_chembl_id'] = kw['pk']
            del kw['pk']
            datas['resource_url'] = cell._build_reverse_url(detail_name, kwargs=kw)
        return bundle

#-----------------------------------------------------------------------------------------------------------------------