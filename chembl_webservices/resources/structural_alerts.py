__author__ = 'mnowotka'

import time
import base64
from tastypie import http
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from tastypie import fields
from tastypie.resources import ALL
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.core.utils import NUMBER_FILTERS, CHAR_FILTERS, FLAG_FILTERS
from chembl_webservices.resources.image import SUPPORTED_ENGINES
from tastypie.resources import ALL, ALL_WITH_RELATIONS
from chembl_webservices.core.utils import COLOR_NAMES
from chembl_webservices.core.utils import options
from chembl_webservices.core.utils import render_indigo
from chembl_webservices.core.utils import render_rdkit
from chembl_webservices.core.utils import highlight_substructure_rdkit
from chembl_webservices.core.utils import highlight_substructure_indigo
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings
from tastypie.exceptions import ImmediateHttpResponse
from collections import defaultdict

try:
    from chembl_compatibility.models import CompoundStructuralAlerts
except ImportError:
    from chembl_core_model.models import CompoundStructuralAlerts

try:
    from chembl_compatibility.models import StructuralAlerts
except ImportError:
    from chembl_core_model.models import StructuralAlerts

try:
    from chembl_compatibility.models import StructuralAlertSets
except ImportError:
    from chembl_core_model.models import StructuralAlertSets

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

try:
    WS_DEBUG = settings.WS_DEBUG
except AttributeError:
    WS_DEBUG = False

dd = defaultdict(lambda:(0,0,0))
options.elemDict=dd

#-----------------------------------------------------------------------------------------------------------------------

class StructuralAlertSetsResource(ChemblModelResource):

    class Meta(ChemblResourceMeta):
        queryset = StructuralAlertSets.objects.all()
        resource_name = 'structural_alert_set'
        collection_name = 'structural_alert_sets'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})

        fields = (
            'set_name',
            'priority',
        )
        filtering = {
            'set_name' : CHAR_FILTERS,
            'priority' : NUMBER_FILTERS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or 'canonical_smiles' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

class StructuralAlertsResource(ChemblModelResource):

    alert_set = fields.ForeignKey('chembl_webservices.resources.structural_alerts.StructuralAlertSetsResource',
        'alertset', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = StructuralAlerts.objects.all()
        resource_name = 'structural_alert'
        collection_name = 'structural_alerts'
        serializer = ChEMBLApiSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['alertset']

        fields = (
            'alert_id',
            'alert_name',
            'smarts',
        )

        filtering = {
            'alert_id' : NUMBER_FILTERS,
            'alert_name': CHAR_FILTERS,
            'smarts': CHAR_FILTERS,
            'alert_set' : ALL_WITH_RELATIONS,
        }

        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or 'canonical_smiles' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

class ImageAwareSerializer(ChEMBLApiSerializer):

    formats = ['xml', 'json', 'jsonp', 'yaml', 'png', 'svg']

    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'urlencode': 'application/x-www-form-urlencoded',
        'png': 'image/png',
        'svg': 'image/svg',
    }

#-----------------------------------------------------------------------------------------------------------------------

class CompoundStructuralAlertsResource(ChemblModelResource):

    molecule_chembl_id = fields.CharField('molecule__chembl_id')
    alert = fields.ForeignKey('chembl_webservices.resources.structural_alerts.StructuralAlertsResource',
        'alert', full=True, null=True, blank=True)

    class Meta(ChemblResourceMeta):
        queryset = CompoundStructuralAlerts.objects.all()
        resource_name = 'compound_structural_alert'
        collection_name = 'compound_structural_alerts'
        serializer = ImageAwareSerializer(resource_name, {collection_name : resource_name})
        prefetch_related = ['alert', 'molecule', 'molecule__chembl']
        fields = (
        )
        filtering = {
            'alert' : ALL_WITH_RELATIONS,
            'molecule_chembl_id': ALL,
        }
        ordering = [field for field in filtering.keys() if not ('comment' in field or 'description' in field or 'canonical_smiles' in field) ]

#-----------------------------------------------------------------------------------------------------------------------

    def get_detail_impl(self, request, base_bundle, **kwargs):
        try:
            obj, in_cache = self.cached_obj_get(bundle=base_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        frmt = request.format

        if not frmt:
            if 'HTTP_ACCEPT' in request.META:
                if request.META['HTTP_ACCEPT'] == 'image/svg':
                    frmt = 'svg'
                elif request.META['HTTP_ACCEPT'] == 'image/png':
                    frmt = 'png'
                request.format = frmt

        if frmt in ['png', 'svg']:
            get_failed = False
            cache_key = self.generate_cache_key('image', **dict({'is_ajax': request.is_ajax()}, **kwargs))
            try:
                ret = self._meta.cache.get(cache_key)
                in_cache = True
            except Exception:
                ret = None
                get_failed = True
                self.log.error('Cashing get exception', exc_info=True, extra=kwargs)

            if ret is None:
                in_cache = False
                ret = self.render_image(obj, request, **kwargs)
                if not get_failed:
                    try:
                        self._meta.cache.set(cache_key, ret)
                    except Exception:
                        self.log.error('Cashing set exception', exc_info=True, extra=kwargs)
            return ret, in_cache

        else:
            bundle = self.build_bundle(obj=obj, request=request)
            bundle = self.full_dehydrate(bundle)
            bundle = self.alter_detail_data_to_serialize(request, bundle)
            return bundle, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def render_image(self, obj, request, **kwargs):
        frmt = getattr(request, 'format', self._meta.default_format)
        try:
            size = int(kwargs.get("dimensions", 500))
        except ValueError:
            return self.answerBadRequest(request, "Image dimensions supplied are invalid")
        ignoreCoords = kwargs.get("ignoreCoords", False)

        bgColor = kwargs.get("bgColor")
        if bgColor and isinstance(bgColor, basestring):
            bgColor = bgColor.lower()
            if bgColor in COLOR_NAMES:
                options.bgColor = COLOR_NAMES[bgColor]
            else:
                options.bgColor = None
        else:
            options.bgColor = None

        if size < 1 or size > 500:
            return self.answerBadRequest(request, "Image dimensions supplied are invalid, max value is 500")

        if frmt == 'png':
            engine = kwargs.get("engine", 'rdkit').lower()
            if engine not in SUPPORTED_ENGINES:
                return self.answerBadRequest(request, "Unsupported engine %s" % engine)
            img, mimetype = self.render_png(obj, size, engine, ignoreCoords)
            if request.is_ajax():
                img = base64.b64encode(img)
        elif frmt == 'svg':
            engine = kwargs.get("engine", 'rdkit').lower()
            if engine not in SUPPORTED_ENGINES:
                return self.answerBadRequest(request, "Unsupported engine %s" % engine)
            img, mimetype = self.render_svg(obj, size, engine, ignoreCoords)
        response = HttpResponse(mimetype=mimetype)
        response.write(img)
        return response

#-----------------------------------------------------------------------------------------------------------------------

    def render_svg(self, obj, size, engine, ignoreCoords):

        ret = None
        molstring = obj.molecule.compoundstructures.molfile
        smarts = obj.alert.smarts

        if engine == 'rdkit':
            highlight = highlight_substructure_rdkit(molstring, smarts)
            if not highlight:
                raise ImmediateHttpResponse(response=http.HttpNotFound())
            mol, matching = highlight
            ret = render_rdkit(mol, matching, options, 'svg', size, ignoreCoords)

        elif engine == 'indigo':
            mol = highlight_substructure_indigo(molstring, smarts)
            if not mol:
                raise ImmediateHttpResponse(response=http.HttpNotFound())
            ret = render_indigo(mol, options, 'svg', 10, size, False, ignoreCoords)

        return ret, "image/svg+xml"

#-----------------------------------------------------------------------------------------------------------------------

    def render_png(self, obj, size, engine, ignoreCoords):

        molstring = obj.molecule.compoundstructures.molfile
        smarts = obj.alert.smarts
        ret = None

        if engine == 'rdkit':
            fontSize = int(size / 33)
            if size < 200:
                fontSize = 1
            options.atomLabelFontSize = fontSize
            highlight = highlight_substructure_rdkit(molstring, smarts)
            if not highlight:
                raise ImmediateHttpResponse(response=http.HttpNotFound())
            mol, matching = highlight
            ret = render_rdkit(mol, matching, options, 'png', size, ignoreCoords)

        elif engine == 'indigo':
            mol = highlight_substructure_indigo(molstring, smarts)
            if not mol:
                raise ImmediateHttpResponse(response=http.HttpNotFound())
            ret = render_indigo(mol, options, 'png', 10, size, False, ignoreCoords)

        return ret, "image/png"

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

        limit = kwargs.get('limit', '') if ('list' in args or 'search' in args) else ''
        offset = kwargs.get('offset', '') if ('list' in args or 'search' in args) else ''
        bgColor = kwargs.get('bgColor', '').lower()
        format = kwargs.get('format', 'png')
        engine = kwargs.get('engine', 'rdkit')
        dimensions = kwargs.get('dimensions', 500)
        ignoreCoords = kwargs.get("ignoreCoords", False)
        is_ajax  = kwargs.get("is_ajax", 2)

        for key, value in filters.items():
            smooshed.append("%s=%s" % (key, value))

        # Use a list plus a ``.join()`` because it's faster than concatenation.
        cache_key =  "%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, '|'.join(args),
                                str(limit), str(offset),'|'.join(order_bits), '|'.join(sorted(smooshed)), str(format),
                                                     str(engine), str(dimensions), str(ignoreCoords), str(is_ajax),
                                                     bgColor)
        return cache_key


#-----------------------------------------------------------------------------------------------------------------------

    def response(self, f):

        def get_something(request, **kwargs):
            start = time.time()
            basic_bundle = self.build_bundle(request=request)

            ret = f(request, basic_bundle, **kwargs)
            if isinstance(ret, tuple) and len(ret) == 2:
                bundle, in_cache = ret
            else:
                return ret

            if not type(bundle) == HttpResponse:
                res = self.create_response(request, bundle)
            else:
                res = bundle

            if WS_DEBUG:
                end = time.time()
                res['X-ChEMBL-in-cache'] = in_cache
                res['X-ChEMBL-retrieval-time'] = end - start
            return res

        return get_something

#-----------------------------------------------------------------------------------------------------------------------