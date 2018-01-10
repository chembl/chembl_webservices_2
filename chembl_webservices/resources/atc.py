__author__ = 'mnowotka'

import time
from tastypie import http
from tastypie.exceptions import BadRequest
from tastypie.exceptions import ImmediateHttpResponse
from django.core.exceptions import ObjectDoesNotExist
from chembl_webservices.core.utils import CHAR_FILTERS
from chembl_webservices.core.resource import WS_DEBUG
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
try:
    from chembl_compatibility.models import AtcClassification
except ImportError:
    from chembl_core_model.models import AtcClassification

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

# ----------------------------------------------------------------------------------------------------------------------


class AtcResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = AtcClassification.objects.all()
        resource_name = 'atc_class'
        collection_name = 'atc'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name: resource_name})
        filtering = {
            'level1': CHAR_FILTERS,
            'level1_description': CHAR_FILTERS,
            'level2': CHAR_FILTERS,
            'level2_description': CHAR_FILTERS,
            'level3': CHAR_FILTERS,
            'level3_description': CHAR_FILTERS,
            'level4': CHAR_FILTERS,
            'level4_description': CHAR_FILTERS,
            'level5': CHAR_FILTERS,
            'who_id': CHAR_FILTERS,
            'who_name': CHAR_FILTERS,
        }
        ordering = filtering.keys()

# ----------------------------------------------------------------------------------------------------------------------

    def get_level(self, pk):
        length = len(pk)
        if length == 7:
            return "level5"
        if length == 1:
            return "level1"
        if length == 3:
            return "level2"
        if length == 4:
            return "level3"
        if length == 5:
            return "level4"
        raise ImmediateHttpResponse(response=http.HttpNotFound())

# ----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
        filters = {}
        stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()])
        pk = kwargs.get('pk')
        if pk:
            del kwargs['pk']
            level = self.get_level(pk)
            kwargs[level] = pk
        filters.update(kwargs)
        applicable_filters, distinct = self.build_filters(filters=filters)

        try:
            objects = self.apply_filters(bundle.request, applicable_filters)
            if distinct:
                objects = objects.distinct()
            if objects.count() <= 0:
                raise ObjectDoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                         (self._meta.object_class.__name__, stringified_kwargs))
            return self.authorized_read_list(objects, bundle)
        except TypeError as e:
            if e.message.startswith('Related Field has invalid lookup:'):
                raise BadRequest(e.message)
            else:
                raise e
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")

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
            objects = obj.get('atc', [])
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
                bundles.append(self.full_dehydrate(bundle, for_list=True))

            obj[self._meta.collection_name] = bundles
            obj = self.alter_list_data_to_serialize(request, obj)

            return obj, in_cache

# ----------------------------------------------------------------------------------------------------------------------
