__author__ = 'mnowotka'

from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.throttle import BaseThrottle
from tastypie.cache import SimpleCache
from chembl_webservices.core.pagination import ChEMBLPaginator

#-----------------------------------------------------------------------------------------------------------------------

class ChemblResourceMeta:
    resource_name = None
    collection_name = None
    detail_uri_name = 'pk'
    include_resource_uri = False
    allowed_methods = ['get']
    prefetch_related = []
    default_format = 'application/xml'
    authentication = Authentication()
    authorization = Authorization()
    throttle = BaseThrottle(throttle_at=100)
    paginator_class = ChEMBLPaginator
    cache = SimpleCache(timeout=30000000) #TODO:  from Django 1.7 you can set TIMEOUT to None so that, by default, cache keys never expire. So exactly what I'm trying to achieve here.

#-----------------------------------------------------------------------------------------------------------------------
