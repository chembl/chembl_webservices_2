__author__ = 'mnowotka'

from tastypie.resources import ALL, ALL_WITH_RELATIONS
import time
import warnings
from collections import OrderedDict
from tastypie import fields
from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from django.db.models.constants import LOOKUP_SEP
from django.db import DatabaseError
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import NoReverseMatch
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from chembl_webservices.resources.molecule import MoleculeResource
from tastypie.exceptions import InvalidSortError
from tastypie.exceptions import ImmediateHttpResponse

try:
    from chembl_compatibility.models import CompoundMols
except ImportError:
    from chembl_core_model.models import CompoundMols

try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

try:
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeHierarchy

try:
    WS_DEBUG = settings.WS_DEBUG
except AttributeError:
    WS_DEBUG = False


#-----------------------------------------------------------------------------------------------------------------------

class SimilarityResource(MoleculeResource):

    similarity = fields.DecimalField('similarity')

    class Meta(MoleculeResource.Meta):
        queryset = MoleculeDictionary.objects.all()
        resource_name = 'similarity'
        required_params = {'api_dispatch_detail' : ['smiles', 'similarity']}

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):

        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)/(?P<similarity>\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)/(?P<similarity>\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])/(?P<similarity>\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])/(?P<similarity>\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<smiles>[^jx]+)/(?P<similarity>\d[\d]*)\.(?P<format>json|xml)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<smiles>[^jx]+)/(?P<similarity>\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, bundle, **kwargs):
        smiles = kwargs.pop('smiles', None)
        std_inchi_key = kwargs.pop('standard_inchi_key', None)
        chembl_id = kwargs.pop('chembl_id', None)

        if not smiles and not std_inchi_key and not chembl_id:
            raise BadRequest("Structure or identifier required.")

        similarity = kwargs.pop('similarity')
        if not similarity:
            raise BadRequest("Similarity parameter is required.")
        else:
            try:
                sim = int(similarity)
                if sim < 70 or sim > 100:
                    raise BadRequest("Invalid Similarity Score supplied: %s" % similarity)
            except ValueError:
                raise BadRequest("Invalid Similarity Score supplied: %s" % similarity)
        if not smiles:
            if chembl_id:
                mol_filters = {'chembl_id':chembl_id}
            else:
                mol_filters = {'compoundstructures__standard_inchi_key' : std_inchi_key}
            try:
                objects = self.apply_filters(bundle.request, mol_filters).values_list('compoundstructures__canonical_smiles',
                    flat=True)
                stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in mol_filters.items()])
                length = len(objects)
                if length <= 0:
                    raise ObjectDoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                                               (self._meta.object_class.__name__, stringified_kwargs))
                elif length > 1:
                    raise MultipleObjectsReturned("More than '%s' matched '%s'." % (self._meta.object_class.__name__,
                                                                                    stringified_kwargs))
                smiles = objects[0]
            except TypeError as e:
                if e.message.startswith('Related Field has invalid lookup:'):
                    raise BadRequest(e.message)
                else:
                    raise e
            except ValueError:
                raise BadRequest("Invalid resource lookup data provided (mismatched type).")

        similar = CompoundMols.objects.similar_to(smiles, similarity).values_list('molecule_id', 'similarity')

        try:
            similarity_map = OrderedDict(sorted(similar, key=lambda x: x[1]))
        except DatabaseError as e:
            self._handle_database_error(e, bundle.request, {'smiles': smiles})

        filters = {
            'chembl__entity_type':'COMPOUND',
            'compoundstructures__isnull' : False,
            'pk__in' : MoleculeHierarchy.objects.all().values_list('parent_molecule_id'),
            'compoundproperties__isnull' : False,
        }

        standard_filters, distinct = self.build_filters(filters=kwargs)

        filters.update(standard_filters)
        try:
            objects = self.get_object_list(bundle.request).filter(**filters).filter(pk__in=[sim[0] for sim in similar])
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")
        if distinct:
            objects = objects.distinct()
        request = bundle.request
        all_request_params = request.GET.copy()
        all_request_params.update(request.POST)
        objects = self.apply_sorting(objects, similarity_map, options=all_request_params)
        return self.authorized_read_list(objects, bundle)

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_list(self, request=None, **kwargs):
        """
        A version of ``obj_get_list`` that uses the cache as a means to get
        commonly-accessed data faster.
        """

        kwargs = self.unqote_args(kwargs)

        cache_key = self.generate_cache_key('list', **kwargs)
        get_failed = False
        in_cache = True

        try:
            obj_list = self._meta.cache.get(cache_key)
        except Exception:
            obj_list = None
            get_failed = True
            self.log.error('Caching get exception', exc_info=True, extra={'request': request,})

        if obj_list is None:
            in_cache = False
            obj_list = self.obj_get_list(request=request, **kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, obj_list)
                except Exception:
                    self.log.error('Caching set exception', exc_info=True, extra={'request': request,})

        return obj_list, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        #       impossible.
        start = time.time()
        base_bundle = self.build_bundle(request=request)
        objects, in_cache = self.cached_obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs))

        paginator_info = {'limit': int(kwargs.pop('limit', getattr(settings, 'API_LIMIT_PER_PAGE', 20))), 'offset': int(kwargs.pop('offset', 0))}

        paginator = self._meta.paginator_class(paginator_info, objects, resource_uri=self.get_resource_uri(),
            limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name,
                method=request.method, params=self.remove_api_resource_names(kwargs))
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = []

        for obj in to_be_serialized[self._meta.collection_name]:
            bundle = self.build_bundle(obj=obj, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        to_be_serialized[self._meta.collection_name] = bundles
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        res = self.create_response(request, to_be_serialized)
        if WS_DEBUG:
            end = time.time()
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start
        return res

#-----------------------------------------------------------------------------------------------------------------------

    def apply_sorting(self, obj_list, similarity_map, options=None):
        """
        Given a dictionary of options, apply some ORM-level sorting to the
        provided ``QuerySet``.

        Looks for the ``order_by`` key and handles either ascending (just the
        field name) or descending (the field name with a ``-`` in front).

        The field name should be the resource field, **NOT** model field.
        """
        if options is None:
            options = {}

        parameter_name = 'order_by'

        if not 'order_by' in options:
            if not 'sort_by' in options:
                # Nothing to alter the order. Return what we've got.
                options['order_by'] = '-similarity'
            else:
                warnings.warn("'sort_by' is a deprecated parameter. Please use 'order_by' instead.")
                parameter_name = 'sort_by'

        order_by_args = []

        if hasattr(options, 'getlist'):
            order_bits = options.getlist(parameter_name)
        else:
            order_bits = options.get(parameter_name)

            if not isinstance(order_bits, (list, tuple)):
                order_bits = [order_bits]

        if (order_bits.index('similarity') == 0 if 'similarity' in order_bits else False) or \
                    (order_bits.index('-similarity') == 0 if '-similarity' in order_bits else False):
            obj_list = self.prefetch_related(obj_list)
            for obj in obj_list:
                sim = similarity_map[obj.molregno]
                obj.similarity = sim
                similarity_map[obj.molregno] = obj
            vals = [sim for sim in similarity_map.values() if type(sim) == MoleculeDictionary]
            return vals if 'similarity' in order_bits else list(reversed(vals))

        else:

            for order_by in order_bits:
                order_by_bits = order_by.split(LOOKUP_SEP)

                field_name = order_by_bits[0]
                order = ''

                if order_by_bits[0].startswith('-'):
                    field_name = order_by_bits[0][1:]
                    order = '-'

                if not field_name in self.fields:
                    # It's not a field we know about. Move along citizen.
                    raise InvalidSortError("No matching '%s' field for ordering on." % field_name)

                if not field_name in self._meta.ordering:
                    raise InvalidSortError("The '%s' field does not allow ordering." % field_name)

                if self.fields[field_name].attribute is None:
                    raise InvalidSortError("The '%s' field has no 'attribute' for ordering with." % field_name)

                order_by_args.append("%s%s" % (order, LOOKUP_SEP.join([self.fields[field_name].attribute] + order_by_bits[1:])))

            obj_list = self.prefetch_related(obj_list.order_by(*order_by_args))
            for obj in obj_list:
                obj.similarity = similarity_map[obj.molregno]
            return obj_list

#-----------------------------------------------------------------------------------------------------------------------

    def get_resource_uri(self, bundle_or_obj=None, url_name='dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'dispatch_detail'

        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

#-----------------------------------------------------------------------------------------------------------------------

    def remove_api_resource_names(self, kwargs):
        return super(MoleculeResource, self).remove_api_resource_names(kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def generate_cache_key(self, *args, **kwargs):
        smooshed = []

        pk = kwargs.get('smiles', None)
        if not pk:
            pk = kwargs.get('standard_inchi_key', None)
        if not pk:
            pk = kwargs.get('chembl_id', None)

        similarity = kwargs.get('similarity', 0)

        fil = {k: v for k,v in kwargs.iteritems() if k not in
                                                  ('smiles', 'standard_inchi_key', 'chembl_id', 'similarity', 'bundle')}

        filters, _ = self.build_filters(fil)

        parameter_name = 'order_by' if 'order_by' in kwargs else 'sort_by'
        if hasattr(kwargs, 'getlist'):
            order_bits = kwargs.getlist(parameter_name, [])
        else:
            order_bits = kwargs.get(parameter_name, [])

        if isinstance(order_bits, basestring):
            order_bits = [order_bits]

        for key, value in filters.items():
            smooshed.append("%s=%s" % (key, value))

        # Use a list plus a ``.join()`` because it's faster than concatenation.
        cache_key =  "%s:%s:%s:%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, '|'.join(args), pk,
                                               str(similarity), '|'.join(order_bits), '|'.join(sorted(smooshed)))
        return cache_key

#-----------------------------------------------------------------------------------------------------------------------
