__author__ = 'mnowotka'

from tastypie.api import Api
from django.http import HttpResponseRedirect
from django.conf import settings

#-----------------------------------------------------------------------------------------------------------------------

try:
    TOP_LEVEL_PAGE = settings.WS_TOP_LEVEL
except AttributeError:
    TOP_LEVEL_PAGE = 'https://www.ebi.ac.uk/chembl/ws'

#-----------------------------------------------------------------------------------------------------------------------

class ChEMBLApi(Api):
        def top_level(self, request, api_name=None):
            return HttpResponseRedirect(TOP_LEVEL_PAGE)

#-----------------------------------------------------------------------------------------------------------------------
