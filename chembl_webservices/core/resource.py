__author__ = 'mnowotka'

import warnings
from tastypie.exceptions import InvalidSortError

import re
import time
import logging
import itertools
from urllib import unquote
from tastypie import http
from tastypie.exceptions import BadRequest
from tastypie.exceptions import UnsupportedFormat
from tastypie.exceptions import Unauthorized
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.exceptions import InvalidFilterError
from tastypie.resources import ModelResource
from tastypie.resources import convert_post_to_put
from tastypie.utils import dict_strip_unicode_keys
from tastypie.utils.mime import build_content_type
from tastypie.exceptions import NotFound
from tastypie import fields
from django.utils import six
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import Http404
from django.conf.urls import url
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.conf import settings
from django.core.signals import got_request_exception
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ValidationError
from django.core.exceptions import FieldError
from django.core.exceptions import TooManyFieldsSent
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from django.db import DatabaseError
from chembl_webservices.core.utils import represents_int
from chembl_webservices.core.utils import list_flatten
from chembl_webservices.core.utils import unpack_request_params

try:
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet()
except:
    sqs = None

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

# ----------------------------------------------------------------------------------------------------------------------


class ChemblModelResource(ModelResource):

    def __init__(self):
        self.log = logging.getLogger(__name__)
        super(ModelResource, self).__init__()

# ----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        """
        Returns a URL scheme based on the default scheme to specify
        the response format as a file extension, e.g. /api/v1/users.json
        """
        return [
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/set/(?P<%s_list>\w[\w/;-]*)\.(?P<format>\w+)$" % (self._meta.resource_name,  self._meta.detail_uri_name), self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)\.(?P<format>\w+)$" % (self._meta.resource_name, self._meta.detail_uri_name), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def determine_format(self, request):
        """
        Used to determine the desired format from the request.format
        attribute.
        """
        if (hasattr(request, 'format') and
                request.format in self._meta.serializer.formats):
            return self._meta.serializer.get_mime_for_format(request.format)
        return super(ChemblModelResource, self).determine_format(request)

# ----------------------------------------------------------------------------------------------------------------------

    def answerBadRequest(self, request, error):
        response_class = http.HttpBadRequest
        data = {'exception': error}
        if request:
            desired_format = self.determine_format(request)
            try:
                serialized = self.serialize(request, data, desired_format)
            except UnsupportedFormat:
                desired_format = 'application/xml'
                serialized = self.serialize(request, data, desired_format)
        else:
            desired_format = 'application/xml'
            serialized = self._meta.serializer.serialize(data, desired_format, None)
        raise ImmediateHttpResponse(response=response_class(content=serialized,
                                                            content_type=build_content_type(desired_format)))

# ----------------------------------------------------------------------------------------------------------------------

    def get_datatables(self, request, **kwargs):
        """
        Returns a serialized form of the schema of the resource.

        Calls ``build_schema`` to generate the data. This method only responds
        to HTTP GET.

        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        self.log_throttled_access(request)
        bundle = self.build_bundle(request=request)
        self.authorized_read_detail(self.get_object_list(bundle.request), bundle)
        return self.create_response(request, self.build_columns_info())

# ----------------------------------------------------------------------------------------------------------------------

    def build_columns_info(self):
        columns = []
        core_fields = set([k for k, v in self.fields.items() if not getattr(v, 'is_related', False)])
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_related', False):
                if field_object.use_in != 'all':
                    continue
                column = dict()
                column["title"] = field_name.replace('_', ' ')
                column["data"] = field_name
                if field_object.null:
                    column["defaultContent"] = "<i>Not set</i>"
                if field_name in self._meta.ordering:
                    column["orderable"] = True
                else:
                    column["orderable"] = False
                columns.append(column)
            elif not getattr(field_object, 'is_m2m', False):
                related_columns = field_object.get_related_resource(None).build_columns_info()
                for r in related_columns["columns"]:
                    if r["data"] in core_fields:
                        continue
                    r["data"] = field_name + "." + r["data"]
                    columns.append(r)
        return {"columns": columns}

# ----------------------------------------------------------------------------------------------------------------------

    def build_schema(self):
        data = super(ChemblModelResource, self).build_schema()
        for field_name, field_object in self.fields.items():
            if getattr(field_object, 'is_related', False):
                nested_schema = field_object.get_related_resource(None).build_schema()
                del nested_schema['allowed_detail_http_methods']
                del nested_schema['allowed_list_http_methods']
                del nested_schema['default_format']
                del nested_schema['default_limit']
                data['fields'][field_name]['schema'] = nested_schema
        return data

# ----------------------------------------------------------------------------------------------------------------------

    def apply_sorting(self, obj_list, options=None):
        try:
            if options is None:
                options = {}

            parameter_name = 'order_by'

            if not 'order_by' in options:
                if not 'sort_by' in options:
                    return obj_list.order_by('pk')
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

                field = self.fields[field_name]
                if getattr(field, 'is_related', False) and len(order_by_bits) == 2:
                    related_resource = field.get_related_resource(None)
                    related_field_name = order_by_bits[1]
                    if related_field_name in related_resource.fields:
                        order_by_args.append("%s%s" %
                                             (order,
                                              LOOKUP_SEP.join([self.fields[field_name].attribute] +
                                                              [related_resource.fields[related_field_name].attribute])))
                        continue

                order_by_args.append("%s%s" %
                                     (order, LOOKUP_SEP.join([self.fields[field_name].attribute] + order_by_bits[1:])))

            return obj_list.order_by(*order_by_args)
        except FieldError as e:
            return self.answerBadRequest(None, e)

# ----------------------------------------------------------------------------------------------------------------------

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            try:
                request.format = kwargs.get('format', None)
                request.POST.dict()  # touch this dict here to populate data, strange problem with Django...

                if request.method == 'GET':
                    kwargs.update(dict(unpack_request_params(request.GET.lists())))

                elif request.method == 'POST':
                    post_arg = dict()
                    if request.META.get('CONTENT_TYPE', 'application/json').startswith(
                        ('multipart/form-data', 'multipart/form-data')):
                        post_arg = dict(unpack_request_params(request.POST.lists()))
                    elif request.body:
                        post_arg = self.deserialize(request, request.body,
                                                    format=request.META.get('CONTENT_TYPE', 'application/json'))
                    kwargs.update(post_arg)

                request.format = kwargs.pop('format', None)

                if 'chembl_id' in kwargs and isinstance(kwargs['chembl_id'], basestring):
                    kwargs['chembl_id'] = kwargs['chembl_id'].upper()

                if 'chembl_id_list' in kwargs and isinstance(kwargs['chembl_id_list'], basestring):
                    kwargs['chembl_id_list'] = kwargs['chembl_id_list'].upper()

                callback = getattr(self, view)
                response = callback(request, *args, **kwargs)

                # Our response can vary based on a number of factors, use
                # the cache class to determine what we should ``Vary`` on so
                # caches won't return the wrong (cached) version.
                varies = getattr(self._meta.cache, "varies", [])

                if varies:
                    patch_vary_headers(response, varies)

                if self._meta.cache.cacheable(request, response):
                    if self._meta.cache.cache_control():
                        # If the request is cacheable and we have a
                        # ``Cache-Control`` available then patch the header.
                        patch_cache_control(response, **self._meta.cache.cache_control())

                if request.is_ajax() and not response.has_header("Cache-Control"):
                    # IE excessively caches XMLHttpRequests, so we're disabling
                    # the browser cache here.
                    # See http://www.enhanceie.com/ie/bugs.asp for details.
                    patch_cache_control(response, no_cache=True)

                return response

            except (BadRequest, fields.ApiFieldError) as e:
                data = {"error_message": e.args[0] if getattr(e, 'args') else ''}
                return self.error_response(request, data, response_class=http.HttpBadRequest)
            except ValidationError as e:
                data = {"error_message": e.messages}
                return self.error_response(request, data, response_class=http.HttpBadRequest)
            except TooManyFieldsSent:
                return self.error_response(request, {"error_message": 'Too many fields send. If you use "__in" filter '
                                                                      'you should aggregate IDs in an array, please '
                                                                      'refer to the ChEMBL API documentation.'},
                                           response_class=http.HttpBadRequest)
            except Exception as e:
                if hasattr(e, 'response'):
                    return e.response

                # A real, non-expected exception.
                # Handle the case where the full traceback is more helpful
                # than the serialized error.
                if settings.DEBUG and getattr(settings, 'TASTYPIE_FULL_DEBUG', False):
                    raise

                # Re-raise the error to get a proper traceback when the error
                # happend during a test case
                if request.META.get('SERVER_NAME') == 'testserver':
                    raise

                # Rather than re-raising, we're going to things similar to
                # what Django does. The difference is returning a serialized
                # error message.
                return self._handle_500(request, e)

        return wrapper

# ----------------------------------------------------------------------------------------------------------------------

    def unquote_args(self, args):
        if isinstance(args, basestring):
            if '%10' in args:
                return args
            return unquote(args)
        elif hasattr(args, '__iter__'):
            if type(args) == dict:
                for key in args:
                    args[key] = self.unquote_args(args[key])
            elif type(args) == list:
                for idx, arg in enumerate(args):
                    args[idx] = self.unquote_args(arg)
        return args

# ----------------------------------------------------------------------------------------------------------------------

    def _handle_database_error(self, error, request, kwargs):
        msg = str(error.message)
        if 'MDL-1622' in msg:
            raise BadRequest("Input string %s is not a valid SMILES string" % kwargs.get('smiles'))
        if 'MDL-2063' in msg:
            raise BadRequest("Input string %s is not a valid SMILES string or ChEMBL ID or InChI Key" % kwargs.get('smiles'))
        elif 'MDL-0280' in msg:
            raise BadRequest("The query %s did not set any substructure keys, and thus cannot be used in a similarity "
                             "search. Use a different query." % kwargs.get('smiles'))
        elif 'MDL-0632' in msg:
            raise BadRequest("Molfile containing R-group atoms is not supported, got: %s" % kwargs.get('smiles'))
        elif 'MDL-0336' in msg:
            raise BadRequest("Input string is empty")
        elif 'MDL-1250' in msg:
            raise BadRequest("SIMILAR search query can not be a NOSTRUCT or unconnected H or LP atom, got: %s" %
                             kwargs.get('smiles'))
        elif 'MDL-1941' in msg:
            raise BadRequest('Error in molecule perception, please correct your query.')
        elif 'ORA-127' in msg:
            m = re.search('ORA-127[23]\d: (?P<desc>.*)',msg)
            if m:
                raise BadRequest("%s" % m.groupdict().get('desc','Invalid regular expression'))
        elif 'Full-text search' in msg:
            raise BadRequest("Full text search is not implemented yet.")
        else:
            raise ImmediateHttpResponse(response=self._handle_500(request, error))


# ----------------------------------------------------------------------------------------------------------------------

    def extract_models(self, chunk):
        ret = []
        for c in chunk:
            obj = c.object
            obj.score = c.score
            ret.append(obj)
        return ret

# ----------------------------------------------------------------------------------------------------------------------
    def list_cache_handler(self, data_provider):

        def handle(bundle, cache_key_name, url_name, **kwargs):
            """
            A version of ``obj_get_list`` that uses the cache as a means to get
            commonly-accessed data faster.
            """
            kwargs = self.unquote_args(kwargs)

            request = bundle.request
            get_failed = False

            try:
                limit = int(re.search(r'^\d+',
                                      str(kwargs.pop('limit', getattr(settings, 'API_LIMIT_PER_PAGE', "20")))).group())
            except(ValueError, AttributeError):
                limit = int(getattr(settings, 'API_LIMIT_PER_PAGE', 20))

            try:
                offset = int(re.search(r'^\d+', str(kwargs.pop('offset', "0"))).group())
            except(ValueError, AttributeError):
                offset = 0

            paginator_info = {'limit': limit, 'offset': offset}
            max_limit = self._meta.max_limit

            try:
                start_slice = (paginator_info['offset'] / max_limit) * max_limit
                end_slice = ((paginator_info['offset'] + paginator_info['limit']) / max_limit) * max_limit
            except ValueError:
                raise BadRequest("Invalid limit or offset provided. Please provide integers.")
            if start_slice == end_slice:
                pages = [{'offset': start_slice, 'limit': max_limit}]
            else:
                pages = [{'offset': start_slice, 'limit': max_limit}, {'offset': end_slice, 'limit': max_limit}]

            for page in pages:
                if get_failed:
                    page['in_cache'] = False
                    continue
                page_kwargs = kwargs.copy()
                page_kwargs.update(page)
                cache_key = self.generate_cache_key(cache_key_name, **page_kwargs)
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
                    self.log.error('Caching get exception', exc_info=True, extra={'bundle': request.path,})

            in_cache = all(page.get('in_cache') for page in pages) and \
                                                        (len(pages) == 1 or pages[0]['count'] == pages[1]['count'])
            if not in_cache:
                sorted_objects = data_provider(bundle, **kwargs)
                is_sqs = False
                if isinstance(sorted_objects, SearchQuerySet):
                    is_sqs = True
                try:
                    count = sorted_objects.count() if not isinstance(sorted_objects, list) else len(sorted_objects)
                except (DatabaseError, NotImplementedError) as e:
                    self._handle_database_error(e, request, kwargs)
                if count < max_limit:
                    len(sorted_objects)
                objs = []
                paginator = self._meta.paginator_class(paginator_info,
                                                       sorted_objects,
                                                       resource_uri=self.get_resource_uri(None, url_name),
                                                       limit=self._meta.limit,
                                                       max_limit=self._meta.max_limit,
                                                       collection_name=self._meta.collection_name,
                                                       format=request.format,
                                                       params=kwargs,
                                                       method=request.method)
                meta = paginator.get_meta(False)
                meta['total_count'] = count
                if request.method.upper() == 'GET':
                    meta['previous'] = paginator.get_previous(paginator.get_limit(), paginator.get_offset())
                    meta['next'] = paginator.get_next(paginator.get_limit(), paginator.get_offset(),
                                                      meta['total_count'])
                for page in pages:
                    if page.get('in_cache') and page.get('count') == meta.get('total_count'):
                        objs.extend(page.get('slice'))
                    else:
                        paginator = self._meta.paginator_class(page,
                                                               sorted_objects,
                                                               resource_uri=self.get_resource_uri(None, url_name),
                                                               limit=self._meta.limit,
                                                               max_limit=self._meta.max_limit,
                                                               collection_name=self._meta.collection_name,
                                                               format=request.format,
                                                               params=kwargs,
                                                               method=request.method)
                        slice = paginator.get_slice(paginator.get_limit(), paginator.get_offset())
                        if is_sqs:
                            slice = self.extract_models(slice)
                        len(slice)
                        objs.extend(slice)
                        if not get_failed:
                            try:
                                slice = list(slice)
                                if slice:
                                    cache_args = self._get_cache_args()
                                    cache_data = {
                                        'slice': slice,
                                        'count': meta.get('total_count'),
                                        'offset': offset,
                                        'url': request.path,
                                        'slice_length': len(slice)
                                    }
                                    cache_data.update(cache_args)
                                    self._meta.cache.set(
                                        page.get('cache_key'), cache_data
                                    )
                            except Exception:
                                self.log.error('Caching set exception', exc_info=True, extra={'bundle': request.path, })
                                get_failed = False

            else:
                objs = list(itertools.chain.from_iterable([page.get('slice') for page in pages]))
                paginator = self._meta.paginator_class(paginator_info,
                                                       [],
                                                       resource_uri=self.get_resource_uri(None, url_name),
                                                       limit=self._meta.limit,
                                                       max_limit=self._meta.max_limit,
                                                       collection_name=self._meta.collection_name,
                                                       format=request.format,
                                                       params=kwargs,
                                                       method=request.method)
                meta = paginator.get_meta(False)
                meta['total_count'] = pages[0]['count']
                if request.method.upper() == 'GET':
                    meta['previous'] = paginator.get_previous(paginator.get_limit(), paginator.get_offset())
                    meta['next'] = paginator.get_next(paginator.get_limit(), paginator.get_offset(),
                                                      meta['total_count'])

            offset = meta.get('offset') - start_slice

            obj_list = {
                self._meta.collection_name: objs[offset:offset + meta.get('limit')],
                'page_meta': meta,
            }

            return obj_list, in_cache

        return handle

# ----------------------------------------------------------------------------------------------------------------------

    def get_search_results(self, user_query):

        res = []

        try:
            queryset = self._meta.queryset
            model = queryset.model
            res = sqs.models(model).load_all().auto_query(user_query).order_by('-score')
        except Exception as e:
            self.log.error('Searching exception', exc_info=True, extra={'user_query': user_query, })
        return res

# ----------------------------------------------------------------------------------------------------------------------

    def check_user_search_query(self, user_query):
        if len(user_query) < 3:
            raise BadRequest('Search query too short')

# ----------------------------------------------------------------------------------------------------------------------

    def evaluate_results(self, results):
        return dict(results.values_list('pk', 'score'))

# ----------------------------------------------------------------------------------------------------------------------

    def search_source(self, bundle, **kwargs):

        user_query = kwargs.get('q')

        if not user_query:
            self.log.error('Empty user query', exc_info=True, extra={'bundle': bundle, 'kwargs': kwargs})
            raise BadRequest('No search query provided')

        if user_query and not isinstance(user_query, unicode):
            user_query = user_query.decode('utf-8')

        self.check_user_search_query(user_query)

        try:
            if not sqs:
                self.log.error('No search query set', exc_info=True, extra={'request': user_query, })
                return self._meta.queryset.none()
        except Exception as e:
            self.log.error('Search error in search_resource', exc_info=True, extra={'request': user_query, })
            return self._meta.queryset.none()

        queryset = getattr(self._meta, 'haystack_queryset', self._meta.queryset)
        res = self.get_search_results(user_query.lower())
        filters = {}

        if hasattr(bundle.request, 'GET'):
            # Grab a mutable copy.
            filters = dict(unpack_request_params(bundle.request.GET.lists()))

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters, distinct = self.build_filters(filters=filters)
        if not applicable_filters and isinstance(res, SearchQuerySet):
            return res
        if not isinstance(res, dict):
            res = self.evaluate_results(res)
        try:
            objects = self.chain_filters(queryset.filter(pk__in=res.keys()), applicable_filters)
            if distinct:
                to_defer = [f.name for f in objects.model._meta.fields if 'TextField' in f.__class__.__name__]
                objects = objects.defer(*to_defer).distinct()
            objects = self.authorized_read_list(objects, bundle)
            objects = self.prefetch_related(objects, **kwargs)
            if res.keys() and isinstance(res.keys()[0], int):
                for obj in objects:
                    obj.score = float(int(res[obj.pk]))
            else:
                for obj in objects:
                    obj.score = float(res[str(obj.pk)])
            return sorted(objects, key=lambda obj: obj.score, reverse=True)

        except TypeError as e:
            if 'invalid lookup' in e.message:
                raise BadRequest(e.message)
            else:
                raise e
        except FieldError as e:
            if 'invalid lookup' in e.message:
                raise BadRequest(e.message)
            else:
                raise e
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")


# ----------------------------------------------------------------------------------------------------------------------

    def list_source(self, bundle, **kwargs):
        objects = self.obj_get_list(bundle=bundle, **kwargs)
        sorted_objects = self.apply_sorting(objects, options=kwargs)
        sorted_objects = self.prefetch_related(sorted_objects, **kwargs)
        return sorted_objects

# ----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_list(self, bundle, **kwargs):
        return self.list_cache_handler(self.list_source)(bundle, 'list', 'api_dispatch_list', **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_search(self, bundle, **kwargs):
        return self.list_cache_handler(self.search_source)(bundle, 'search', 'api_get_search', **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def detail_cache_handler(self, f):

        def handle(bundle, cache_key, **kwargs):
            """
            A version of ``obj_get`` that uses the cache as a means to get
            commonly-accessed data faster.
            """
            cache_key = self.generate_cache_key(cache_key, **kwargs)
            get_failed = False
            in_cache = True

            try:
                cached_bundle = self._meta.cache.get(cache_key)
            except Exception:
                cached_bundle = None
                get_failed = True
                self.log.error('Caching get exception', exc_info=True, extra={'bundle': bundle.request.path, })

            if cached_bundle is None:
                in_cache = False
                cached_bundle = f(bundle=bundle, **kwargs)
                if not get_failed:
                    try:
                        self._meta.cache.set(cache_key, cached_bundle)
                    except Exception:
                        self.log.error('Caching set exception', exc_info=True, extra={'bundle': bundle.request.path, })

            return cached_bundle, in_cache
        return handle

# ----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get(self, bundle, **kwargs):
        """
        A version of ``obj_get`` that uses the cache as a means to get
        commonly-accessed data faster.
        """

        return self.detail_cache_handler(self.obj_get)(bundle, 'detail', **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def response(self, f):

        def get_something(request, **kwargs):
            start = time.time()
            basic_bundle = self.build_bundle(request=request)

            ret = f(request, basic_bundle, **kwargs)
            if isinstance(ret, tuple) and len(ret) == 2:
                bundle, in_cache = ret
            else:
                return ret

            res = self.create_response(request, bundle)
            if WS_DEBUG:
                end = time.time()
                res['X-ChEMBL-in-cache'] = in_cache
                res['X-ChEMBL-retrieval-time'] = end - start
            return res

        return get_something

# ----------------------------------------------------------------------------------------------------------------------

    def full_dehydrate(self, bundle, for_list=False, for_search=False, **kwargs):
        """
        Given a bundle with an object instance, extract the information from it
        to populate the resource.
        """
        if not for_search:
            use_in = ['all', 'list' if for_list else 'detail']
        else:
            use_in = ['all', 'search']
        only = kwargs.get('only')
        if only and isinstance(only, basestring):
            only = [x.strip() for x in only.split(',')]

        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            # If it's not for use in this mode, skip
            if only and all([field_name not in x for x in only]):
                continue
            field_use_in = getattr(field_object, 'use_in', 'all')
            if callable(field_use_in):
                if not field_use_in(bundle):
                    continue
            else:
                if field_use_in not in use_in:
                    continue

            # A touch leaky but it makes URI resolution work.
            if getattr(field_object, 'dehydrated_type', None) == 'related':
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            bundle.data[field_name] = field_object.dehydrate(bundle, for_list=for_list)

            # Check for an optional method to do further dehydration.
            method = getattr(self, "dehydrate_%s" % field_name, None)

            if method:
                bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)
        return bundle

# ----------------------------------------------------------------------------------------------------------------------

    def serialise_list(self,f, for_list, for_search):

        def handler(request, base_bundle, **kwargs):
            to_be_serialized, in_cache = f(bundle=base_bundle,
                                           **self.remove_api_resource_names(kwargs))

            # Dehydrate the bundles in preparation for serialization.
            bundles = []

            for obj in to_be_serialized[self._meta.collection_name]:
                bundle = self.build_bundle(obj=obj, request=request)
                bundles.append(self.full_dehydrate(bundle, for_list=for_list, for_search=for_search, **kwargs))

            to_be_serialized[self._meta.collection_name] = bundles
            to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)

            return to_be_serialized, in_cache

        return handler

# ----------------------------------------------------------------------------------------------------------------------

    def get_list_impl(self, request, base_bundle, **kwargs):
        return self.serialise_list(self.cached_obj_get_list, for_list=True, for_search=False)(
                                                    request, base_bundle, **self.remove_api_resource_names(kwargs))

# ----------------------------------------------------------------------------------------------------------------------

    def get_list(self, request, **kwargs):
        return self.response(self.get_list_impl)(request, **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def get_search_impl(self, request, base_bundle, **kwargs):
        return self.serialise_list(self.cached_obj_get_search, for_list=False, for_search=True)(
                                                    request, base_bundle, **self.remove_api_resource_names(kwargs))

# ----------------------------------------------------------------------------------------------------------------------

    def get_search(self, request, **kwargs):
        return self.response(self.get_search_impl)(request, **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def get_detail(self, request, **kwargs):
        """
        Returns a single serialized resource.

        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        return self.response(self.get_detail_impl)(request, **kwargs)

# ----------------------------------------------------------------------------------------------------------------------

    def get_detail_impl(self, request, base_bundle, **kwargs):
        try:
            obj, in_cache = self.cached_obj_get(bundle=base_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle, **kwargs)
        bundle = self.alter_detail_data_to_serialize(request, bundle)

        return bundle, in_cache

# ----------------------------------------------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------------------------------------------

    def preprocess_filters(self, filters, for_cache_key=False):
        return filters

# ----------------------------------------------------------------------------------------------------------------------

    def build_filters(self, filters=None, ignore_bad_filters=False, for_cache_key=False):

        distinct = False
        if filters is None:
            filters = {}
        filters = self.preprocess_filters(filters, for_cache_key)

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
                elif filter_expr == 'only':
                    if isinstance(value, basestring):
                        value = [x.strip() for x in value.split(',')]
                    if filter_expr in qs_filters:
                        qs_filters[filter_expr].extend(value)
                    else:
                        qs_filters[filter_expr] = [value]
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            try:
                lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            except InvalidFilterError:
                if ignore_bad_filters:
                    continue
                elif for_cache_key:
                    qs_filters[filter_expr] = value
                    continue
                else:
                    raise
            if any([x.endswith('_set') for x in lookup_bits]):
                distinct = True
                lookup_bits = map(lambda x: x[0:-4] if x.endswith('_set') else x, lookup_bits)
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters), distinct

# ----------------------------------------------------------------------------------------------------------------------

    def prefetch_related(self, objects, **kwargs):
        only = kwargs.get('only')
        if only and not isinstance(only, list):
            only = [x.strip().split(LOOKUP_SEP)[0] for x in only.split(',')]
        related_fields = getattr(self._meta, 'prefetch_related', None)
        if only and all([not self.fields[field].is_m2m for field in only if field in self.fields]):
            only = list_flatten(only)
            only_related = set([self.fields[field].attribute for field in only if ((field in self.fields) and
                                                                                   (getattr(self.fields[field], 'is_related', False)))])
            related_attrs = set([field if isinstance(field, str) else
                                 field.prefetch_through for field in related_fields])
            intersection = only_related & related_attrs
            if intersection:
                return objects.prefetch_related(*list(intersection))
            return objects
        if not related_fields:
            return objects
        return objects.prefetch_related(*self._meta.prefetch_related)

# ----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.

        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        try:
            applicable_filters, distinct = self.build_filters(filters=kwargs)
            object_list = self.chain_filters(self.get_object_list(bundle.request), applicable_filters)
            if distinct:
                to_defer = [f.name for f in object_list.model._meta.fields if 'TextField' in f.__class__.__name__]
                object_list = object_list.defer(*to_defer).distinct()
            object_list = self.prefetch_related(object_list, **kwargs)
            stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()])

            if len(object_list) <= 0:
                raise ObjectDoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                                           (self._meta.object_class.__name__, stringified_kwargs))
            elif len(object_list) > 1:
                raise MultipleObjectsReturned("More than '%s' matched '%s'." %
                                              (self._meta.object_class.__name__, stringified_kwargs))

            bundle.obj = object_list[0]
            self.authorized_read_detail(object_list, bundle)
            return bundle.obj
        except ValueError:
            raise ImmediateHttpResponse(response=http.HttpNotFound())

# ----------------------------------------------------------------------------------------------------------------------

    def chain_filters(self, query, applicable_filters):
        only = applicable_filters.get('only')
        if only:
            del applicable_filters['only']
            if isinstance(only, basestring):
                only = only.split(',')
            only = list(set(list_flatten(only)))
        ret = query
        list_filters = self.normalise_filters(applicable_filters)
        for filtr in list_filters:
            ret = ret.filter(**filtr)
        if only and all([not self.fields[field].is_m2m for field in only if field in self.fields]):
            ret = ret.only(*[self.fields[field].attribute for field in only if field in self.fields])
        return ret

# ----------------------------------------------------------------------------------------------------------------------

    def apply_filters(self, request, applicable_filters):
        """
        An ORM-specific implementation of ``apply_filters``.

        The default simply applies the ``applicable_filters`` as ``**kwargs``,
        but should make it possible to do more advanced things.
        """
        try:
            return self.chain_filters(self.get_object_list(request), applicable_filters)
        except (TypeError, FieldError) as e:
            if any('chembl_id' in filtr for filtr in applicable_filters):
                applicable_filters = {
                    k.replace('chembl_id', 'chembl__chembl_id'): v for (k, v) in applicable_filters.items()}
                return self.chain_filters(self.get_object_list(request), applicable_filters)
            raise TypeError(e.message)


# ----------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def normalise_filters(applicable_filters):
        if not applicable_filters:
            return []
        for key in applicable_filters:
            if not (isinstance(applicable_filters[key], list) or isinstance(applicable_filters[key], tuple)) or \
                    key.endswith('__in') or key.endswith('__range'):
                applicable_filters[key] = [applicable_filters[key]]
        # reserve as much *distinct* dicts as the longest sequence
        result = [{} for i in range(max(map(len, applicable_filters.values())))]
        # fill each dict, one key at a time
        for k, seq in applicable_filters.items():
            for oneDict, oneValue in zip(result, seq):
                oneDict[k] = oneValue
        return result

# ----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
        filters = {}

        if hasattr(bundle.request, 'GET'):
            # Grab a mutable copy.
            filters = dict(unpack_request_params(bundle.request.GET.lists()))

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters, distinct = self.build_filters(filters=filters)

        try:
            objects = self.apply_filters(bundle.request, applicable_filters)
            if distinct:
                to_defer = [f.name for f in objects.model._meta.fields if 'TextField' in f.__class__.__name__]
                objects = objects.defer(*to_defer).distinct()
            return self.authorized_read_list(objects, bundle)
        except TypeError as e:
            if e.message.startswith('Related Field has invalid lookup:') \
                    or e.message.startswith('Related Field got invalid lookup:'):
                raise BadRequest(e.message)
            else:
                raise e
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")

# ----------------------------------------------------------------------------------------------------------------------

    def filter_value_to_python(self, value, field_name, filters, filter_expr, filter_type):
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
        if filter_type == 'range':
            if len(value) != 2 or not represents_int(value[0]) or not represents_int(value[1]):
                raise BadRequest(
                    "Invalid range: should consist of two integers separated by comma, got {0} instead.".format(value))
        return value

# ----------------------------------------------------------------------------------------------------------------------

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
                bundle = self.full_dehydrate(bundle, for_list=True, **kwargs)
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

# ----------------------------------------------------------------------------------------------------------------------

    def _handle_500(self, request, exception):
        import traceback
        import sys
        the_trace = '\n'.join(traceback.format_exception(*(sys.exc_info())))
        response_class = http.HttpApplicationError
        response_code = 500

        not_found_exceptions = (NotFound, ObjectDoesNotExist, Http404)

        if isinstance(exception, not_found_exceptions):
            response_class = HttpResponseNotFound
            response_code = 404

        detailed_data = {
            "error_message": six.text_type(exception),
            "traceback": the_trace,
        }
        self.log.error('_handle_500 error', exc_info=True, extra={'data': detailed_data, 'request': request,
                                                                  'original_exception': exception})
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
        if 400 <= response_code < 500:
            data = {
                "error_message": six.text_type(exception),
            }

        else:
            data = {
                "error_message": getattr(settings, 'TASTYPIE_CANNED_ERROR',
                                         "Sorry, this request could not be processed. Please try again later."),
            }

        return self.error_response(request, data, response_class=response_class)

# ----------------------------------------------------------------------------------------------------------------------

    def _get_cache_args(self, *args, **kwargs):
        from collections import OrderedDict

        cache_ordered_dict = OrderedDict()
        smooshed = []

        filters, _ = self.build_filters(kwargs)

        parameter_name = 'order_by' if 'order_by' in kwargs else 'sort_by'
        if hasattr(kwargs, 'getlist'):
            order_bits = kwargs.getlist(parameter_name, [])
        else:
            order_bits = kwargs.get(parameter_name, [])

        if isinstance(order_bits, basestring):
            order_bits = [order_bits]

        limit = kwargs.get('limit', '') if ('list' in args or 'search' in args) else ''
        offset = kwargs.get('offset', '') if ('list' in args or 'search' in args) else ''
        query = kwargs.get('q', '') if 'search' in args else ''
        only = kwargs.get('only', '')

        for key, value in filters.items():
            smooshed.append("%s=%s" % (key, value))

        if isinstance(query, unicode):
            query = query.encode('utf-8')

        cache_ordered_dict['api_name'] = self._meta.api_name
        cache_ordered_dict['resource_name'] = self._meta.resource_name
        cache_ordered_dict['args'] = '|'.join(args)
        cache_ordered_dict['limit'] = str(limit)
        cache_ordered_dict['offset'] = str(offset)
        cache_ordered_dict['only'] = str(only)
        cache_ordered_dict['query'] = query
        cache_ordered_dict['order'] = '|'.join(order_bits)
        cache_ordered_dict['filters'] = '|'.join(sorted(smooshed))

        return cache_ordered_dict

# ----------------------------------------------------------------------------------------------------------------------

    def generate_cache_key(self, *args, **kwargs):

        cache_ordered_dict = self._get_cache_args(*args, **kwargs)
        ret = ':'.join(str(x) for x in cache_ordered_dict.values())
        return ret

# ----------------------------------------------------------------------------------------------------------------------
