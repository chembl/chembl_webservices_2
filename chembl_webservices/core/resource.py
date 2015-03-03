__author__ = 'mnowotka'

import time
import logging
import mimeparse
import itertools
from urllib import unquote
from tastypie import http
from tastypie.exceptions import BadRequest
from tastypie.exceptions import Unauthorized
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import ModelResource
from tastypie.resources import convert_post_to_put
from tastypie.utils import dict_strip_unicode_keys
from tastypie.exceptions import NotFound
from django.utils import six
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import Http404
from django.conf.urls import url
from django.conf import settings
from django.core.signals import got_request_exception
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from django.db import DatabaseError

# If ``csrf_exempt`` isn't present, stub it.
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(func):
        return func

try:
    WS_DEBUG = settings.WS_DEBUG
except AttributeError:
    WS_DEBUG = False

#-----------------------------------------------------------------------------------------------------------------------

class ChemblModelResource(ModelResource):

#-----------------------------------------------------------------------------------------------------------------------

    def __init__(self):
        self.log = logging.getLogger(__name__)
        super(ModelResource, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if (hasattr(request, 'format') and
                request.format in self._meta.serializer.formats):
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(ChemblModelResource, self).determine_format(request)

#-----------------------------------------------------------------------------------------------------------------------

    def flatten_django_lists(self, lists):
        ret = []
        for x in lists:
            first, second = x
            if type(second) == list and len(second) == 1 and isinstance(second[0], basestring):
                ret.append((first, second[0]))
            else:
                ret.append(x)
        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.get('format', None)
            request.POST.dict() # touch this dict here ti populate data, strange problem with Django...

            if request.method == 'GET':
                kwargs.update(dict(self.flatten_django_lists(request.GET.lists())))

            elif request.method == 'POST':
                if request.META.get('CONTENT_TYPE', 'application/json').startswith(
                    ('multipart/form-data', 'multipart/form-data')):
                    post_arg = dict(self.flatten_django_lists(request.POST.lists()))
                else:
                    post_arg = self.deserialize(request, request.body,
                        format=request.META.get('CONTENT_TYPE', 'application/json'))
                kwargs.update(post_arg)

            request.format = kwargs.pop('format', None)

            if 'chembl_id' in kwargs and isinstance(kwargs['chembl_id'], basestring):
                kwargs['chembl_id'] = kwargs['chembl_id'].upper()

            if 'chembl_id_list' in kwargs and isinstance(kwargs['chembl_id_list'], basestring):
                kwargs['chembl_id_list'] = kwargs['chembl_id_list'].upper()

            wrapped_view = super(ChemblModelResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)

        return wrapper

#-----------------------------------------------------------------------------------------------------------------------

    def unqote_args(self, args):
        if isinstance(args, basestring):
            return unquote(args)
        elif hasattr(args, '__iter__'):
            if type(args) == dict:
                for key in args:
                    args[key] = self.unqote_args(args[key])
            elif type(args) == list:
                for idx, arg in enumerate(args):
                    args[idx] = self.unqote_args(arg)
        return args

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_list(self, bundle, **kwargs):
        """
        A version of ``obj_get_list`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        kwargs = self.unqote_args(kwargs)

        request = bundle.request
        get_failed = False
        paginator_info = {'limit': int(kwargs.pop('limit', getattr(settings, 'API_LIMIT_PER_PAGE', 20))), 'offset': int(kwargs.pop('offset', 0))}
        max_limit = self._meta.max_limit

        try:
            start_slice = (paginator_info['offset'] / max_limit) * max_limit
            end_slice = ((paginator_info['offset'] + paginator_info['limit']) / max_limit) * max_limit
        except ValueError:
            raise BadRequest("Invalid limit or offset provided. Please provide integers.")
        if start_slice == end_slice:
            pages = [{'offset':start_slice, 'limit':max_limit}]
        else:
            pages = [{'offset':start_slice, 'limit':max_limit}, {'offset':end_slice, 'limit':max_limit}]

        for page in pages:
            if get_failed:
                page['in_cache'] = False
                continue
            page_kwargs = kwargs.copy()
            page_kwargs.update(page)
            cache_key = self.generate_cache_key('list', **page_kwargs)
            page['cache_key'] = cache_key
            try:
                chunk = self._meta.cache.get(cache_key)
                if chunk:
                    page['slice'] = chunk.get('slice')
                    page['count'] = chunk.get('count')
                    page['in_cache'] = True
                else:
                    page['in_cache'] = False
            except Exception as e:
                page['in_cache'] = False
                get_failed = True
                self.log.error('Caching get exception', exc_info=True, extra={'bundle': bundle,})

        in_cache = all(page.get('in_cache') for page in pages) and (len(pages) == 1 or pages[0]['count'] == pages[1]['count'])
        if not in_cache:
            all_request_params = request.GET.copy()
            all_request_params.update(request.POST)
            objects = self.obj_get_list(bundle=bundle, **kwargs)
            sorted_objects = self.apply_sorting(objects, options=all_request_params)
            sorted_objects = self.prefetch_related(sorted_objects)
            try:
                count = sorted_objects.count()
            except DatabaseError as e:
                msg = e.message
                if 'MDL-1622' in str(msg):
                    raise BadRequest("Input string %s is not a valid SMILES string" % kwargs.get('smiles'))
                elif 'MDL-0632' in str(msg):
                    raise BadRequest("Molfile containing R-group atoms is not supported, got: %s" % kwargs.get('smiles'))
                else:
                    raise ImmediateHttpResponse(response=self._handle_500(bundle.request, e))
            if count < max_limit:
                len(sorted_objects)
            objs = []
            paginator = self._meta.paginator_class(paginator_info, sorted_objects, resource_uri=self.get_resource_uri(),
                limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name,
                format=request.format, params=kwargs, method=request.method)
            meta = paginator.get_meta(False)
            meta['total_count'] = count
            if request.method.upper() == 'GET':
                meta['previous'] = paginator.get_previous(paginator.get_limit(), paginator.get_offset())
                meta['next'] = paginator.get_next(paginator.get_limit(), paginator.get_offset(), meta['total_count'])
            for page in pages:
                if page.get('in_cache') and page.get('count') == meta.get('total_count'):
                    objs.extend(page.get('slice'))
                else:
                    paginator = self._meta.paginator_class(page, sorted_objects, resource_uri=self.get_resource_uri(),
                        limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name,
                        format=request.format, params=kwargs, method=request.method)
                    slice = paginator.get_slice(paginator.get_limit(), paginator.get_offset())
                    len(slice)
                    objs.extend(slice)
                    if not get_failed:
                        try:
                            self._meta.cache.set(page.get('cache_key'), {'slice':slice, 'count': meta.get('total_count')})
                        except Exception:
                            self.log.error('Caching set exception', exc_info=True, extra={'bundle': bundle,})
                            get_failed = False

        else:
            objs = list(itertools.chain.from_iterable([page.get('slice') for page in pages]))
            paginator = self._meta.paginator_class(paginator_info, [], resource_uri=self.get_resource_uri(),
                limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name,
                format=request.format, params=kwargs, method=request.method)
            meta = paginator.get_meta(False)
            meta['total_count'] = pages[0]['count']
            if request.method.upper() == 'GET':
                meta['previous'] = paginator.get_previous(paginator.get_limit(), paginator.get_offset())
                meta['next'] = paginator.get_next(paginator.get_limit(), paginator.get_offset(), meta['total_count'])

        offset = meta.get('offset') - start_slice

        obj_list = {
        self._meta.collection_name: objs[offset:offset + meta.get('limit')],
        'page_meta': meta,
        }

        return obj_list, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get(self, bundle, **kwargs):
        """
        A version of ``obj_get`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        cache_key = self.generate_cache_key('detail', **kwargs)
        get_failed = False
        in_cache = True

        try:
            cached_bundle = self._meta.cache.get(cache_key)
        except Exception:
            cached_bundle = None
            get_failed = True
            self.log.error('Caching get exception', exc_info=True, extra={'bundle': bundle,})

        if cached_bundle is None:
            in_cache = False
            cached_bundle = self.obj_get(bundle=bundle, **kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, cached_bundle)
                except Exception:
                    self.log.error('Caching set exception', exc_info=True, extra={'bundle': cached_bundle,})

        return cached_bundle, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def get_list(self, request, **kwargs):
        start = time.time()
        base_bundle = self.build_bundle(request=request)
        to_be_serialized, in_cache = self.cached_obj_get_list(bundle=base_bundle,
            **self.remove_api_resource_names(kwargs))

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

    def get_detail(self, request, **kwargs):
        """
        Returns a single serialized resource.

        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        start = time.time()
        basic_bundle = self.build_bundle(request=request)

        try:
            obj, in_cache = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        res = self.create_response(request, bundle)
        if WS_DEBUG:
            end = time.time()
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start
        return res

#-----------------------------------------------------------------------------------------------------------------------

    def dispatch(self, request_type, request, **kwargs):
        """
        Handles the common operations (allowed HTTP method, authentication,
        throttling, method lookup) surrounding most CRUD interactions.
        """
        allowed_methods = getattr(self._meta, "%s_allowed_methods" % request_type, None)

        if 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
            request.method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']

        request_method = self.method_check(request, allowed=allowed_methods)
        method = getattr(self, "%s_%s" % (request_method, request_type), None)

        if method is None:
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        self.is_authenticated(request)
        self.throttle_check(request)

        # All clear. Process the request.
        request = convert_post_to_put(request)
        response = method(request, **kwargs)

        # Add the throttled request.
        self.log_throttled_access(request)

        # If what comes back isn't a ``HttpResponse``, assume that the
        # request was accepted and that some action occurred. This also
        # prevents Django from freaking out.
        if not isinstance(response, HttpResponse):
            return http.HttpNoContent()

        return response

#-----------------------------------------------------------------------------------------------------------------------

    def build_filters(self, filters=None):

        distinct = False
        if filters is None:
            filters = {}

        qs_filters = {}

        if getattr(self._meta, 'queryset', None) is not None:
            # Get the possible query terms from the current QuerySet.
            query_terms = self._meta.queryset.query.query_terms
        else:
            query_terms = QUERY_TERMS

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if not field_name in self.fields:
                if filter_expr == 'pk' or filter_expr == self._meta.detail_uri_name:
                    qs_filters[filter_expr] = value
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            if any([x.endswith('_set') for x in lookup_bits]):
                distinct = True
                lookup_bits = map(lambda x: x[0:-4] if x.endswith('_set') else x, lookup_bits)
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters), distinct

#-----------------------------------------------------------------------------------------------------------------------

    def prefetch_related(self, objects):
        related_fields = getattr(self._meta, 'prefetch_related', None)
        if not related_fields:
            return objects
        return objects.prefetch_related(*self._meta.prefetch_related)

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.

        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        try:
            applicable_filters, distinct = self.build_filters(filters=kwargs)
            object_list = self.get_object_list(bundle.request).filter(**applicable_filters)
            if distinct:
                object_list = object_list.distinct()
            object_list = self.prefetch_related(object_list)
            stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()])

            if len(object_list) <= 0:
                raise self._meta.object_class.DoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                                           (self._meta.object_class.__name__, stringified_kwargs))
            elif len(object_list) > 1:
                raise MultipleObjectsReturned("More than '%s' matched '%s'." %
                                              (self._meta.object_class.__name__, stringified_kwargs))

            bundle.obj = object_list[0]
            self.authorized_read_detail(object_list, bundle)
            return bundle.obj
        except ValueError:
            raise ImmediateHttpResponse(response=http.HttpNotFound())

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
            filters = dict(self.flatten_django_lists(bundle.request.GET.lists()))

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters, distinct = self.build_filters(filters=filters)

        try:
            objects = self.apply_filters(bundle.request, applicable_filters)
            if distinct:
                objects = objects.distinct()
            return self.authorized_read_list(objects, bundle)
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")

#-----------------------------------------------------------------------------------------------------------------------

    def filter_value_to_python(self, value, field_name, filters, filter_expr,
            filter_type):
        if value in ['true', 'True', True]:
            value = True
        elif value in ['false', 'False', False]:
            value = False
        elif value in ('nil', 'none', 'None', None):
            value = None

        # Split on ',' if not empty string and either an in or range filter.
        if filter_type in ('in', 'range') and len(value):
            if hasattr(filters, 'getlist'):
                value = []

                for part in filters.getlist(filter_expr):
                    if isinstance(part, basestring):
                        value.extend(part.split(','))
                    else:
                        if len(part) == 1 and isinstance(part[0], basestring):
                            value.extend(part[0].split(','))
                        else:
                            value.extend(part)
            else:
                if isinstance(value, basestring):
                    value = value.split(',')
                elif type(value) in (list, tuple) and len(value) == 1 and isinstance(value[0], basestring):
                    value = value[0].split(',')
        return value

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
                obj, _ = self.cached_obj_get(bundle=base_bundle, **{self._meta.detail_uri_name: identifier})
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle, for_list=True)
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

    def _handle_500(self, request, exception):
        import traceback
        import sys
        the_trace = '\n'.join(traceback.format_exception(*(sys.exc_info())))
        response_class = http.HttpApplicationError
        response_code = 500

        NOT_FOUND_EXCEPTIONS = (NotFound, ObjectDoesNotExist, Http404)

        if isinstance(exception, NOT_FOUND_EXCEPTIONS):
            response_class = HttpResponseNotFound
            response_code = 404


        detailed_data = {
            "error_message": six.text_type(exception),
            "traceback": the_trace,
        }
        self.log.error('_handle_500 error', exc_info=True, extra={'data': detailed_data, 'request': request, 'original_exception': exception})
        if settings.DEBUG:
            return self.error_response(request, detailed_data, response_class=response_class)

        # When DEBUG is False, send an error message to the admins (unless it's
        # a 404, in which case we check the setting).
        send_broken_links = getattr(settings, 'SEND_BROKEN_LINK_EMAILS', False)

        if not response_code == 404 or send_broken_links:
            log = logging.getLogger('django.request.tastypie')
            log.error('Internal Server Error: %s' % request.path, exc_info=True,
                      extra={'status_code': response_code, 'request': request})

        # Send the signal so other apps are aware of the exception.
        got_request_exception.send(self.__class__, request=request)

        # Prep the data going out.
        data = {
            "error_message": getattr(settings, 'TASTYPIE_CANNED_ERROR', "Sorry, this request could not be processed. Please try again later."),
        }
        return self.error_response(request, data, response_class=response_class)

#-----------------------------------------------------------------------------------------------------------------------

    def generate_cache_key(self, *args, **kwargs):
        smooshed = []

        filters, _ = self.build_filters(kwargs)

        parameter_name = 'order_by' if 'order_by' in kwargs else 'sort_by'
        if hasattr(kwargs, 'getlist'):
            order_bits = kwargs.getlist(parameter_name, [])
        else:
            order_bits = kwargs.get(parameter_name, [])

        if isinstance(order_bits, basestring):
            order_bits = [order_bits]

        limit = kwargs.get('limit', '') if 'list' in args else ''
        offset = kwargs.get('offset', '') if 'list' in args else ''

        for key, value in filters.items():
            smooshed.append("%s=%s" % (key, value))

        # Use a list plus a ``.join()`` because it's faster than concatenation.
        cache_key =  "%s:%s:%s:%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, '|'.join(args),
                                               str(limit), str(offset),'|'.join(order_bits), '|'.join(sorted(smooshed)))
        return cache_key

#-----------------------------------------------------------------------------------------------------------------------