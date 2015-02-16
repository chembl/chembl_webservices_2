__author__ = 'mnowotka'

import time
from chembl_new_webservices.core.utils import CHAR_FILTERS
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from tastypie import http
from tastypie import fields
from tastypie.utils import trailing_slash
from tastypie.exceptions import BadRequest
from tastypie.exceptions import Unauthorized
from django.conf.urls import url
from django.db.models import Q
from chembl_new_webservices.core.resource import ChemblModelResource
from chembl_new_webservices.core.meta import ChemblResourceMeta
from chembl_new_webservices.core.serialization import ChEMBLApiSerializer
from chembl_new_webservices.core.resource import WS_DEBUG
try:
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeHierarchy
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeFormsResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('molecule__chembl_id')
    parent = fields.CharField('parent_molecule__chembl_id')

    class Meta(ChemblResourceMeta):
        queryset = MoleculeHierarchy.objects.all()
        filtering = {
            'molecule_chembl_id' : CHAR_FILTERS,
            'parent' : CHAR_FILTERS,
        }
        resource_name = 'molecule_form'
        collection_name = 'molecule_forms'
        detail_uri_name = 'molecule__chembl_id'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

#-----------------------------------------------------------------------------------------------------------------------

    def alter_list_data_to_serialize(self, request, data):
        """
        A hook to alter list data just before it gets serialized & sent to the user.

        Useful for restructuring/renaming aspects of the what's going to be
        sent.

        Should accommodate for a list of objects, generally also including
        meta data.
        """
        bundles = data['molecule_forms']
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
        if datas['molecule_chembl_id'] == datas['parent']:
            datas['parent'] = "True"
        else:
            datas['parent'] = "False"
        return bundle

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
        filters = {}

        if hasattr(bundle.request, 'GET'):
            # Grab a mutable copy.
            filters.update(dict(self.flatten_django_lists(bundle.request.GET.lists())))

        if hasattr(bundle.request, 'POST'):
            # Grab a mutable copy.
            filters.update(dict(self.flatten_django_lists(bundle.request.POST.lists())))

        filters.update(kwargs)

        stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()])

        detail_uri_name = self._meta.detail_uri_name

        chembl_id = kwargs.get(detail_uri_name)
        if chembl_id:
            del kwargs[detail_uri_name]
            forms = set()
            try:
                mol = MoleculeDictionary.objects.get(chembl_id=chembl_id)
            except ObjectDoesNotExist:
                return http.HttpNotFound()
            except MultipleObjectsReturned:
                return http.HttpMultipleChoices("More than one resource is found at this URI.")

            if hasattr(mol, 'downgraded') and mol.downgraded:
                return http.HttpNotFound()

            hierarchy = mol.moleculehierarchy

            has_parent, parent_chemblID = (hierarchy.parent_molecule, hierarchy.parent_molecule_id)
            if has_parent:
                parent = has_parent
            else:
                parent, parent_chemblID = (mol, mol.chembl_id)
            forms.add(parent_chemblID)
            forms.update(MoleculeDictionary.objects.filter(moleculehierarchy__parent_molecule=parent)
                                                                    .values_list("pk", flat=True))
            objects = MoleculeHierarchy.objects.filter(parent_molecule_id__in=list(forms))

        else:
            filters.update(kwargs)
            try:
                objects = self.apply_filters(bundle.request, filters)
                #if distinct:
                #    objects = objects.distinct()
            except ValueError:
                raise BadRequest("Invalid resource lookup data provided (mismatched type).")

        return self.authorized_read_list(objects, bundle)

#-----------------------------------------------------------------------------------------------------------------------

    def get_detail(self, request, **kwargs):
        start = time.time()
        basic_bundle = self.build_bundle(request=request)

        try:
            obj, in_cache = self.cached_obj_get_list(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()

        bundles = []

        for ob in obj[self._meta.collection_name]:
            bundle = self.build_bundle(obj=ob, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        obj[self._meta.collection_name] = bundles
        obj = self.alter_list_data_to_serialize(request, obj)
        res = self.create_response(request, obj)
        if WS_DEBUG:
            end = time.time()
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start
        return res

#-----------------------------------------------------------------------------------------------------------------------

    def get_multiple(self, request, **kwargs):
        """
        Returns a serialized list of resources based on the identifiers
        from the URL.

        Calls ``obj_get`` to fetch only the objects requested. This method
        only responds to HTTP GET.

        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Rip apart the list then iterate.
        kwarg_name = '%s_list' % self._meta.detail_uri_name
        obj_identifiers = kwargs.get(kwarg_name, '').split(';')
        objects = []
        not_found = []
        base_bundle = self.build_bundle(request=request)

        for identifier in obj_identifiers:
            try:
                obj = self.obj_get(bundle=base_bundle, **{self._meta.detail_uri_name: identifier})
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle, for_list=True)
                bundle = self.alter_detail_data_to_serialize(request, bundle)
                objects.append(bundle)
            except (ObjectDoesNotExist, Unauthorized):
                not_found.append(identifier)

        object_list = {
            self._meta.collection_name: objects,
        }

        if len(not_found):
            object_list['not_found'] = not_found

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

#-----------------------------------------------------------------------------------------------------------------------

    def apply_filters(self, request, filters):
        """
        An ORM-specific implementation of ``apply_filters``.

        The default simply applies the ``applicable_filters`` as ``**kwargs``,
        but should make it possible to do more advanced things.
        """
        pk = filters.get(self._meta.detail_uri_name)
        if not pk:
            applicable_filters, distinct = self.build_filters(filters=filters)
            objects = super(MoleculeFormsResource, self).apply_filters(request, applicable_filters)
            if distinct:
                objects = objects.distinct()
            return objects

        objects =  self.get_object_list(request).filter(Q(molecule__chembl_id=pk) |
                                                    Q(parent_molecule__chembl_id=pk)).distinct()
        parent = objects[0].parent_molecule.chembl_id
        if parent == pk:
            return objects
        else:
            return self.get_object_list(request).filter(Q(molecule__chembl_id=parent) |
                                                    Q(parent_molecule__chembl_id=parent)).distinct()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):

        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------
