__author__ = 'mnowotka'

import time
import base64
import StringIO
from tastypie.utils import trailing_slash
from tastypie import http
from tastypie.exceptions import NotFound
from tastypie.exceptions import BadRequest
from django.conf.urls import url
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from chembl_beaker.beaker.core_apps.jsonImages.jsonCanvas import MolToJSON
from chembl_beaker.beaker.draw import cairoCanvas
from chembl_beaker.beaker import draw
from chembl_webservices.core.resource import ChemblModelResource
from chembl_webservices.core.resource import WS_DEBUG
from chembl_webservices.core.meta import ChemblResourceMeta
from chembl_webservices.core.serialization import ChEMBLApiSerializer
from chembl_webservices.dis import SineWarp
from chembl_webservices.resources.molecule import MoleculeResource
try:
    from chembl_compatibility.models import CompoundStructures
except ImportError:
    from chembl_core_model.models import CompoundStructures
try:
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeHierarchy
try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

# If ``csrf_exempt`` isn't present, stub it.
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(func):
        return func

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit.Chem import Draw
except ImportError:
    Chem = None
    Draw = None
    AllChem = None

try:
    from chembl_beaker.beaker.draw import DrawingOptions
except ImportError:
    DrawingOptions = None

try:
    import indigo
    import indigo_renderer
except ImportError:
    indigo = None
    indigo_renderer = None

try:
    import cairo
    cffi = False
except ImportError:
    import cairocffi
    cairocffi.install_as_pycairo()
    cffi = True
    import io
    import cairo
    if not hasattr(cairo, 'HAS_PDF_SURFACE'):
        cairo.HAS_PDF_SURFACE = False
    if not hasattr(cairo, 'HAS_SVG_SURFACE'):
        cairo.HAS_SVG_SURFACE = True

SUPPORTED_ENGINES = ['rdkit', 'indigo']

options = DrawingOptions()
options.useFraction = 1.0
options.dblBondOffset = .13

fakeSerializer = ChEMBLApiSerializer('image')
fakeSerializer.formats = ['png', 'svg', 'json']

available_fields = [f.name for f in MoleculeDictionary._meta.fields]

#-----------------------------------------------------------------------------------------------------------------------

class ImageResource(ChemblModelResource):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta(ChemblResourceMeta):
        resource_name = 'image'
        serializer = fakeSerializer
        default_format = 'image/png'
        description = {'api_dispatch_detail' : '''
Get image of the compound, specified by

*  _ChEMBL ID_ or
*  _Standard InChI Key_

You can specify optional parameters:

*  __engine__ - chemistry toolkit used for rendering, can be _rdkit_ or _indigo_, default: _rdkit_.
*  __dimensions__ - size of the image (the length of the square image side). Can't be more than _500_, default: _500_.
*  __ignoreCoords__ - Ignore 2D coordinates encoded in the molfile and let the chemistry toolkit to recompute them.


'''}
        queryset = CompoundStructures.objects.all() if 'downgraded' not in available_fields else \
                        CompoundStructures.objects.exclude(molecule__downgraded=True)


#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<molecule__chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule__chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule__chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])\.(?P<format>png|svg)$" % MoleculeResource._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<molecule__chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)\.(?P<format>png|svg)$" % MoleculeResource._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

#-----------------------------------------------------------------------------------------------------------------------

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):

            if request.method == 'GET':
                kwargs.update(request.GET.dict())

            elif request.method == 'POST':
                if request.META.get('CONTENT_TYPE', 'application/json').startswith(
                    ('multipart/form-data', 'multipart/form-data')):
                    post_arg = request.POST.dict()
                else:
                    post_arg = self.deserialize(request, request.body,
                        format=request.META.get('CONTENT_TYPE', 'application/json'))
                kwargs.update(post_arg)

            request.format = kwargs.get('format', None)

            if 'molecule__chembl_id' in kwargs and isinstance(kwargs['molecule__chembl_id'], basestring):
                kwargs['molecule__chembl_id'] = kwargs['molecule__chembl_id'].upper()

            wrapped_view = super(ChemblModelResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)

        return wrapper

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get(self, **kwargs):
        """
        A version of ``obj_get`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        get_failed = False
        cache_key = self.generate_cache_key('detail', **kwargs)

        try:
            cached_bundle = self._meta.cache.get(cache_key)
        except Exception:
            cached_bundle = None
            get_failed = True
            self.log.error('Caching get exception', exc_info=True, extra={'kwargs': kwargs,})

        if cached_bundle is None:
            cached_bundle = self.obj_get(**kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, cached_bundle)
                except Exception:
                    self.log.error('Caching set exception', exc_info=True, extra={'kwargs': kwargs,})

        return cached_bundle

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, **kwargs):

        chembl_id = kwargs.get('molecule__chembl_id')
        standard_inchi_key = kwargs.get('standard_inchi_key')

        if not chembl_id and not standard_inchi_key:
            raise BadRequest("ChEMBL ID or standard InChi Key required.")

        filters = dict((k,v) for k,v in kwargs.items() if k in ('molecule__chembl_id','standard_inchi_key'))
        stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in filters.items()])

        filters.update({
            'molecule__chembl__entity_type':'COMPOUND',
            'molecule__compoundstructures__isnull' : False,
            'molecule__compoundproperties__isnull' : False,
        })

        try:
            molfile_list = self.get_object_list(None).filter(**filters).values_list('molfile', flat=True)

            if len(molfile_list) <= 0:
                raise ObjectDoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                                           (self._meta.object_class.__name__, stringified_kwargs))
            elif len(molfile_list) > 1:
                raise MultipleObjectsReturned("More than '%s' matched '%s'." %
                                              (self._meta.object_class.__name__, stringified_kwargs))
        except ValueError:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")

        return molfile_list[0]

#-----------------------------------------------------------------------------------------------------------------------

    def render_image(self, mol, request, **kwargs):
        frmt = kwargs.get('format', 'png')
        size = int(kwargs.get("dimensions", 500))
        ignoreCoords = kwargs.get("ignoreCoords", False)

        if size < 1 or size > 500:
            return self.answerBadRequest(request, "Image dimensions supplied are invalid, max value is 500")

        if frmt == 'png':
            engine = kwargs.get("engine", 'rdkit').lower()
            if engine not in SUPPORTED_ENGINES:
                return self.answerBadRequest(request, "Unsupported engine %s" % engine)
            img, mimetype = self.render_png(mol, size, engine, ignoreCoords)
            if request.is_ajax():
                img = base64.b64encode(img)
        elif frmt == 'svg':
            img, mimetype = self.render_svg(mol, size, ignoreCoords)
        elif frmt == 'json':
            img, mimetype = self.render_json(mol, size, ignoreCoords)
        elif frmt == 'chemcha':
            img, mimetype = self.render_chemcha(mol, size, ignoreCoords)
            if request.is_ajax():
                img = base64.b64encode(img)
        else:
            return self.answerBadRequest(request, "Unsupported format %s" % frmt)
        response = HttpResponse(mimetype=mimetype)
        response.write(img)
        return response

#-----------------------------------------------------------------------------------------------------------------------

    def render_svg(self, molstring, size, ignoreCoords):
        mol = Chem.MolFromMolBlock(str(molstring))
        if ignoreCoords:
            AllChem.Compute2DCoords(mol)

        if cffi and cairocffi.version <= (1,10,0) :
            imageData = io.BytesIO()
        else:
            imageData = StringIO.StringIO()
        surf = cairo.SVGSurface(imageData, size, size)
        ctx = cairo.Context(surf)
        canv = cairoCanvas.Canvas(ctx=ctx, size=(size, size), imageType='svg')
        leg = mol.GetProp("_Name") if mol.HasProp("_Name") else None
        draw.MolToImage(mol, size=(size, size), legend=leg, canvas=canv, fitImage=True, options=options)
        canv.flush()
        surf.finish()
        return imageData.getvalue(), 'image/svg+xml'

#-----------------------------------------------------------------------------------------------------------------------

    def render_json(self, molstring, size, ignoreCoords):
        mol = Chem.MolFromMolBlock(str(molstring))
        if ignoreCoords:
            AllChem.Compute2DCoords(mol)

        leg = mol.GetProp("_Name") if mol.HasProp("_Name") else None
        return MolToJSON(mol, size=(size,size), legend=leg, fitImage=True, options=options), 'application/json'

#-----------------------------------------------------------------------------------------------------------------------

    def render_png(self, molstring, size, engine, ignoreCoords):
        buf = StringIO.StringIO()

        if engine == 'rdkit':
            fontSize = int(size / 33)
            if size < 200:
                fontSize = 1
            mol = Chem.MolFromMolBlock(str(molstring))
            if ignoreCoords:
                AllChem.Compute2DCoords(mol)

            options.atomLabelFontSize = fontSize

            image = draw.MolToImage(mol, size=(size, size), fitImage=True, options=options)
            image.save(buf, "PNG")
            return buf.getvalue(), "image/png"

        elif engine == 'indigo':
            indigoObj = indigo.Indigo()
            renderer = indigo_renderer.IndigoRenderer(indigoObj)
            indigoObj.setOption("render-output-format", "png")
            indigoObj.setOption("render-margins", 10, 10)
            indigoObj.setOption("render-image-size", size, size)
            indigoObj.setOption("render-coloring", True)
            indigoObj.setOption("ignore-stereochemistry-errors", "true")
            mol = indigoObj.loadMolecule(str(molstring))
            if ignoreCoords:
                mol.layout()
            image = renderer.renderToBuffer(mol)
            return image.tostring(), "image/png"

#-----------------------------------------------------------------------------------------------------------------------

    def get_detail(self, request, **kwargs):
        cache_key = self.generate_cache_key('image', **kwargs)
        get_failed = False

        in_cache = False
        start = time.time()
        if kwargs.get('format', 'png') == 'chemcha' and '_' in kwargs:
            ret = self.image_get(request, **kwargs)
        else:
            try:
                ret = self._meta.cache.get(cache_key)
                in_cache = True
            except Exception:
                ret = None
                get_failed = True
                self.log.error('Cashing get exception', exc_info=True, extra=kwargs)

            if ret is None:
                in_cache = False
                ret = self.image_get(request, **kwargs)
                if not get_failed:
                    try:
                        self._meta.cache.set(cache_key, ret)
                    except Exception:
                        self.log.error('Cashing set exception', exc_info=True, extra=kwargs)

        if WS_DEBUG:
            end = time.time()
            ret['X-ChEMBL-in-cache'] = in_cache
            ret['X-ChEMBL-retrieval-time'] = end - start
        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def image_get(self, request, **kwargs):
        try:
            mol = self.cached_obj_get(**kwargs)
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        return self.render_image(mol, request, **kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def render_chemcha(self, molstring, size, ignoreCoords):
        buf = StringIO.StringIO()
        fontSize = int(size / 33)
        if size < 200:
            fontSize = 1
        mol = Chem.MolFromMolBlock(str(molstring))
        if ignoreCoords:
            AllChem.Compute2DCoords(mol)

        if DrawingOptions:
            options = DrawingOptions()
            options.useFraction = 1.0
            options.dblBondOffset = .13
            options.atomLabelFontSize = fontSize
        else:
            options={"useFraction": 1.0,
                     "dblBondOffset": .13,
                     'atomLabelFontSize': fontSize,}
        image = Draw.MolToImage(mol, size=(size, size), fitImage=True, options=options)
        image = SineWarp().render(image)
        image.save(buf, "PNG")
        return buf.getvalue(), "image/png"

#-----------------------------------------------------------------------------------------------------------------------

    def generate_cache_key(self, *args, **kwargs):

        molecule__chembl_id = kwargs.get('molecule__chembl_id', '')
        standard_inchi_key = kwargs.get('standard_inchi_key', '')
        format = kwargs.get('format', 'png')
        engine = kwargs.get('engine', 'rdkit')
        dimensions = kwargs.get('dimensions', 500)
        ignoreCoords = kwargs.get("ignoreCoords", False)


        # Use a list plus a ``.join()`` because it's faster than concatenation.
        cache_key =  "%s:%s:%s:%s:%s:%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, '|'.join(args),
                                                     str(molecule__chembl_id), str(standard_inchi_key), str(format),
                                                     str(engine), str(dimensions), str(ignoreCoords))
        return cache_key

#-----------------------------------------------------------------------------------------------------------------------