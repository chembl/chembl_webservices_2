__author__ = 'mnowotka'

from tastypie.paginator import Paginator
from tastypie.paginator import urlencode
from tastypie.paginator import six

#-----------------------------------------------------------------------------------------------------------------------

def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

#-----------------------------------------------------------------------------------------------------------------------

class ChEMBLPaginator(Paginator):

    def __init__(self, request_data, objects, resource_uri=None, limit=None, offset=0, max_limit=1000,
                 collection_name='objects', format=None, params=None, method=None):
        """
        Instantiates the ``Paginator`` and allows for some configuration.

        The ``request_data`` argument ought to be a dictionary-like object.
        May provide ``limit`` and/or ``offset`` to override the defaults.
        Commonly provided ``request.GET``. Required.

        The ``objects`` should be a list-like object of ``Resources``.
        This is typically a ``QuerySet`` but can be anything that
        implements slicing. Required.

        Optionally accepts a ``limit`` argument, which specifies how many
        items to show at a time. Defaults to ``None``, which is no limit.

        Optionally accepts an ``offset`` argument, which specifies where in
        the ``objects`` to start displaying results from. Defaults to 0.

        Optionally accepts a ``max_limit`` argument, which the upper bound
        limit. Defaults to ``1000``. If you set it to 0 or ``None``, no upper
        bound will be enforced.
        """
        self.request_data = request_data
        self.objects = objects
        self.limit = limit
        self.max_limit = max_limit
        self.offset = offset
        self.resource_uri = resource_uri
        self.collection_name = collection_name
        self.format = format
        self.params = params
        self.method = method

#-----------------------------------------------------------------------------------------------------------------------

    def _generate_uri(self, limit, offset):
        if self.resource_uri is None:
            return None

        try:
            # QueryDict has a urlencode method that can handle multiple values for the same key
            request_params = self.request_data.copy()
            if 'limit' in request_params:
                del request_params['limit']
            if 'offset' in request_params:
                del request_params['offset']
            request_params.update({'limit': limit, 'offset': offset})
            if self.params:
                request_params.update(self.params)
            encoded_params = request_params.urlencode()
        except AttributeError:
            encoded_params = encoded_dict(request_params)
            encoded_params = urlencode(encoded_params)

        if self.format:
            return '%s.%s?%s' % (
                self.resource_uri,
                self.format,
                encoded_params
            )

        return '%s?%s' % (
            self.resource_uri,
            encoded_params
        )

#-----------------------------------------------------------------------------------------------------------------------

    def page(self):
        """
        Generates all pertinent data about the requested page.

        Handles getting the correct ``limit`` & ``offset``, then slices off
        the correct set of results and returns all pertinent metadata.
        """
        limit = self.get_limit()
        offset = self.get_offset()
        count = self.get_count()
        objects = self.get_slice(limit, offset)
        meta = {
            'offset': offset,
            'limit': limit,
            'total_count': count,
        }

        if limit and self.method.upper() == 'GET':
            meta['previous'] = self.get_previous(limit, offset)
            meta['next'] = self.get_next(limit, offset, count)

        return {
            self.collection_name: objects,
            'page_meta': meta,
        }

#-----------------------------------------------------------------------------------------------------------------------

    def get_meta(self, fetchCount=True):
        limit = self.get_limit()
        offset = self.get_offset()
        count = self.get_count() if fetchCount else None
        meta = {
            'offset': offset,
            'limit': limit,
            'total_count': count,
        }

        return meta

#-----------------------------------------------------------------------------------------------------------------------

class DummyPaginator(object):
    def __init__(self, request_data, objects, resource_uri=None,
                 limit=None, offset=0, max_limit=1000,
                 collection_name='objects', format=None, params=None, method=None):
        self.objects = objects
        self.collection_name = collection_name

    def page(self):
        return { self.collection_name: self.objects, }

#-----------------------------------------------------------------------------------------------------------------------