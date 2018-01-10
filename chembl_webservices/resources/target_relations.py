__author__ = 'mnowotka'

from tastypie import http
from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

try:
    from chembl_compatibility.models import TargetRelations
except ImportError:
    from chembl_core_model.models import TargetRelations
try:
    from chembl_compatibility.models import ChemblIdLookup
except ImportError:
    from chembl_core_model.models import ChemblIdLookup
try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class TargetRelationsResource(ChemblModelResource):

    target_chembl_id = fields.CharField('target__chembl_id')
    related_target_chembl_id = fields.CharField('related_target__chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = TargetRelations.objects.all()
        excludes = ['targrel_id']
        resource_name = 'target_relation'
        collection_name = 'target_relations'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        detail_uri_name = 'target__chembl_id'
        prefetch_related = [
            Prefetch('target', queryset=TargetDictionary.objects.only('chembl')),
            Prefetch('related_target', queryset=TargetDictionary.objects.only('chembl')),
        ]

        fields = (
            'relationship',
        )

        filtering = {
            'target_chembl_id': NUMBER_FILTERS,
            'related_target_chembl_id': CHAR_FILTERS,
            'relationship': CHAR_FILTERS,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or
                                                                'description' in field or 'canonical_smiles' in field)]

# ----------------------------------------------------------------------------------------------------------------------

    def get_detail_impl(self, request, basic_bundle, **kwargs):
        """
        Returns a single serialized resource.

        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """

        try:
            obj, in_cache = self.cached_obj_get_list(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
            objects = obj.get('target_relations', [])
        except ObjectDoesNotExist:
            return http.HttpNotFound()

        if len(objects) == 1:
            object = objects[0]
            bundle = self.build_bundle(obj=object, request=request)
            bundle = self.full_dehydrate(bundle, **kwargs)
            bundle = self.alter_detail_data_to_serialize(request, bundle)
            return self.create_response(request, bundle)
        else:
            bundles = []

            for ob in obj[self._meta.collection_name]:
                bundle = self.build_bundle(obj=ob, request=request)
                bundles.append(self.full_dehydrate(bundle, for_list=True, **kwargs))

            obj[self._meta.collection_name] = bundles
            obj = self.alter_list_data_to_serialize(request, obj)

            return obj, in_cache

# ----------------------------------------------------------------------------------------------------------------------
