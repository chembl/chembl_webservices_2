__author__ = 'mnowotka'

import StringIO
from chembl_beaker.beaker.draw import cairoCanvas
from chembl_beaker.beaker import draw
from collections import defaultdict

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    Chem = None
    Draw = None
    AllChem = None

try:
    from chembl_beaker.beaker.draw import DrawingOptions
except ImportError:
    DrawingOptions = None

NEW_RENDER_ENGINE = False

try:
    from rdkit.Chem.Draw import rdMolDraw2D
    if hasattr(rdMolDraw2D, 'MolDraw2DCairo') and hasattr(rdMolDraw2D, 'MolDraw2DSVG'):
        NEW_RENDER_ENGINE = True
except:
    pass

try:
    import indigo
    from indigo import IndigoException
    import indigo_renderer
    indigoObj = indigo.Indigo()
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

# ----------------------------------------------------------------------------------------------------------------------

options = DrawingOptions()
options.useFraction = 1.0
options.dblBondOffset = .13
options.bgColor = None

NUMBER_FILTERS = ['exact', 'range', 'gt', 'gte', 'lt', 'lte', 'in', 'isnull']
FLAG_FILTERS = ['exact', 'isnull']
CHAR_FILTERS = ['exact', 'iexact', 'contains', 'icontains', 'istartswith', 'startswith', 'endswith', 'iendswith',
                'search', 'regex', 'iregex', 'isnull', 'in']
DATE_FILTERS = ['exact', 'year', 'month', 'day', 'week_day', 'isnull']
STANDARD_RDKIT_COLORS = {16: (0.8, 0.8, 0), 1: (0.55, 0.55, 0.55), 35: (0.5, 0.3, 0.1), 17: (0, 0.8, 0),
                         0: (0.5, 0.5, 0.5), 7: (0, 0, 1), 8: (1, 0, 0), 9: (0.2, 0.8, 0.8), 15: (1, 0.5, 0)}

# ----------------------------------------------------------------------------------------------------------------------

COLOR_NAMES = {
    'aliceblue': (0.941176, 0.972549, 1),
    'antiquewhite': (0.980392, 0.921569, 0.843137),
    'aquamarine': (0.498039, 1, 0.831373),
    'azure': (0.941176, 1, 1),
    'beige': (0.960784, 0.960784, 0.862745),
    'bisque': (1, 0.894118, 0.768627),
    'black': (0, 0, 0),
    'blanchedalmond': (1, 0.921569, 0.803922),
    'blue': (0, 0, 1),
    'blueviolet': (0.541176, 0.168627, 0.886275),
    'brown': (0.647059, 0.164706, 0.164706),
    'burlywood': (0.870588, 0.721569, 0.529412),
    'cadetblue': (0.372549, 0.619608, 0.627451),
    'chartreuse': (0.498039, 1, 0),
    'chocolate': (0.823529, 0.411765, 0.117647),
    'coral': (1, 0.498039, 0.313725),
    'cornflowerblue': (0.392157, 0.584314, 0.929412),
    'cornsilk': (1, 0.972549, 0.862745),
    'crimson': (0.862745, 0.0784314, 0.235294),
    'cyan': (0, 1, 1),
    'darkblue': (0, 0, 0.545098),
    'darkcyan': (0, 0.545098, 0.545098),
    'darkgoldenrod': (0.721569, 0.52549, 0.0431373),
    'darkgray': (0.662745, 0.662745, 0.662745),
    'darkgreen': (0, 0.392157, 0),
    'darkgrey': (0.662745, 0.662745, 0.662745),
    'darkkhaki': (0.741176, 0.717647, 0.419608),
    'darkmagenta': (0.545098, 0, 0.545098),
    'darkolivegreen': (0.333333, 0.419608, 0.184314),
    'darkorange': (1, 0.54902, 0),
    'darkorchid': (0.6, 0.196078, 0.8),
    'darkred': (0.545098, 0, 0),
    'darksalmon': (0.913725, 0.588235, 0.478431),
    'darkseagreen': (0.560784, 0.737255, 0.560784),
    'darkslateblue': (0.282353, 0.239216, 0.545098),
    'darkslategray': (0.184314, 0.309804, 0.309804),
    'darkslategrey': (0.184314, 0.309804, 0.309804),
    'darkturquoise': (0, 0.807843, 0.819608),
    'darkviolet': (0.580392, 0, 0.827451),
    'deeppink': (1, 0.0784314, 0.576471),
    'deepskyblue': (0, 0.74902, 1),
    'dimgray': (0.411765, 0.411765, 0.411765),
    'dimgrey': (0.411765, 0.411765, 0.411765),
    'dodgerblue': (0.117647, 0.564706, 1),
    'firebrick': (0.698039, 0.133333, 0.133333),
    'floralwhite': (1, 0.980392, 0.941176),
    'forestgreen': (0.133333, 0.545098, 0.133333),
    'gainsboro': (0.862745, 0.862745, 0.862745),
    'ghostwhite': (0.972549, 0.972549, 1),
    'gold': (1, 0.843137, 0),
    'goldenrod': (0.854902, 0.647059, 0.12549),
    'gray': (0.745098, 0.745098, 0.745098),
    'green': (0, 1, 0),
    'greenyellow': (0.678431, 1, 0.184314),
    'grey': (0.745098, 0.745098, 0.745098),
    'honeydew': (0.941176, 1, 0.941176),
    'hotpink': (1, 0.411765, 0.705882),
    'indianred': (0.803922, 0.360784, 0.360784),
    'indigo': (0.294118, 0, 0.509804),
    'ivory': (1, 1, 0.941176),
    'khaki': (0.941176, 0.901961, 0.54902),
    'lavender': (0.901961, 0.901961, 0.980392),
    'lavenderblush': (1, 0.941176, 0.960784),
    'lawngreen': (0.486275, 0.988235, 0),
    'lemonchiffon': (1, 0.980392, 0.803922),
    'lightblue': (0.678431, 0.847059, 0.901961),
    'lightcoral': (0.941176, 0.501961, 0.501961),
    'lightcyan': (0.878431, 1, 1),
    'lightgoldenrod': (0.933333, 0.866667, 0.509804),
    'lightgoldenrodyellow': (0.980392, 0.980392, 0.823529),
    'lightgray': (0.827451, 0.827451, 0.827451),
    'lightgreen': (0.564706, 0.933333, 0.564706),
    'lightgrey': (0.827451, 0.827451, 0.827451),
    'lightpink': (1, 0.713725, 0.756863),
    'lightsalmon': (1, 0.627451, 0.478431),
    'lightseagreen': (0.12549, 0.698039, 0.666667),
    'lightskyblue': (0.529412, 0.807843, 0.980392),
    'lightslateblue': (0.517647, 0.439216, 1),
    'lightslategray': (0.466667, 0.533333, 0.6),
    'lightslategrey': (0.466667, 0.533333, 0.6),
    'lightsteelblue': (0.690196, 0.768627, 0.870588),
    'lightyellow': (1, 1, 0.878431),
    'limegreen': (0.196078, 0.803922, 0.196078),
    'linen': (0.980392, 0.941176, 0.901961),
    'magenta': (1, 0, 1),
    'maroon': (0.690196, 0.188235, 0.376471),
    'mediumaquamarine': (0.4, 0.803922, 0.666667),
    'mediumblue': (0, 0, 0.803922),
    'mediumorchid': (0.729412, 0.333333, 0.827451),
    'mediumpurple': (0.576471, 0.439216, 0.858824),
    'mediumseagreen': (0.235294, 0.701961, 0.443137),
    'mediumslateblue': (0.482353, 0.407843, 0.933333),
    'mediumspringgreen': (0, 0.980392, 0.603922),
    'mediumturquoise': (0.282353, 0.819608, 0.8),
    'mediumvioletred': (0.780392, 0.0823529, 0.521569),
    'midnightblue': (0.0980392, 0.0980392, 0.439216),
    'mintcream': (0.960784, 1, 0.980392),
    'mistyrose': (1, 0.894118, 0.882353),
    'moccasin': (1, 0.894118, 0.709804),
    'navajowhite': (1, 0.870588, 0.678431),
    'navy': (0, 0, 0.501961),
    'navyblue': (0, 0, 0.501961),
    'oldlace': (0.992157, 0.960784, 0.901961),
    'olivedrab': (0.419608, 0.556863, 0.137255),
    'orange': (1, 0.647059, 0),
    'orangered': (1, 0.270588, 0),
    'orchid': (0.854902, 0.439216, 0.839216),
    'palegoldenrod': (0.933333, 0.909804, 0.666667),
    'palegreen': (0.596078, 0.984314, 0.596078),
    'paleturquoise': (0.686275, 0.933333, 0.933333),
    'palevioletred': (0.858824, 0.439216, 0.576471),
    'papayawhip': (1, 0.937255, 0.835294),
    'peachpuff': (1, 0.854902, 0.72549),
    'peru': (0.803922, 0.521569, 0.247059),
    'pink': (1, 0.752941, 0.796078),
    'plum': (0.866667, 0.627451, 0.866667),
    'powderblue': (0.690196, 0.878431, 0.901961),
    'purple': (0.627451, 0.12549, 0.941176),
    'red': (1, 0, 0),
    'rosybrown': (0.737255, 0.560784, 0.560784),
    'royalblue': (0.254902, 0.411765, 0.882353),
    'saddlebrown': (0.545098, 0.270588, 0.0745098),
    'salmon': (0.980392, 0.501961, 0.447059),
    'sandybrown': (0.956863, 0.643137, 0.376471),
    'seagreen': (0.180392, 0.545098, 0.341176),
    'seashell': (1, 0.960784, 0.933333),
    'sgibeet': (0.556863, 0.219608, 0.556863),
    'sgibrightgray': (0.772549, 0.756863, 0.666667),
    'sgibrightgrey': (0.772549, 0.756863, 0.666667),
    'sgichartreuse': (0.443137, 0.776471, 0.443137),
    'sgidarkgray': (0.333333, 0.333333, 0.333333),
    'sgidarkgrey': (0.333333, 0.333333, 0.333333),
    'sgilightblue': (0.490196, 0.619608, 0.752941),
    'sgilightgray': (0.666667, 0.666667, 0.666667),
    'sgilightgrey': (0.666667, 0.666667, 0.666667),
    'sgimediumgray': (0.517647, 0.517647, 0.517647),
    'sgimediumgrey': (0.517647, 0.517647, 0.517647),
    'sgiolivedrab': (0.556863, 0.556863, 0.219608),
    'sgisalmon': (0.776471, 0.443137, 0.443137),
    'sgislateblue': (0.443137, 0.443137, 0.776471),
    'sgiteal': (0.219608, 0.556863, 0.556863),
    'sgiverydarkgray': (0.156863, 0.156863, 0.156863),
    'sgiverydarkgrey': (0.156863, 0.156863, 0.156863),
    'sgiverylightgray': (0.839216, 0.839216, 0.839216),
    'sgiverylightgrey': (0.839216, 0.839216, 0.839216),
    'sienna': (0.627451, 0.321569, 0.176471),
    'skyblue': (0.529412, 0.807843, 0.921569),
    'slateblue': (0.415686, 0.352941, 0.803922),
    'slategray': (0.439216, 0.501961, 0.564706),
    'slategrey': (0.439216, 0.501961, 0.564706),
    'snow': (1, 0.980392, 0.980392),
    'springgreen': (0, 1, 0.498039),
    'steelblue': (0.27451, 0.509804, 0.705882),
    'tan': (0.823529, 0.705882, 0.54902),
    'thistle': (0.847059, 0.74902, 0.847059),
    'tomato': (1, 0.388235, 0.278431),
    'turquoise': (0.25098, 0.878431, 0.815686),
    'violet': (0.933333, 0.509804, 0.933333),
    'violetred': (0.815686, 0.12549, 0.564706),
    'wheat': (0.960784, 0.870588, 0.701961),
    'white': (1, 1, 1),
    'whitesmoke': (0.960784, 0.960784, 0.960784),
    'yellow': (1, 1, 0),
    'yellowgreen': (0.603922, 0.803922, 0.196078),
}

# ----------------------------------------------------------------------------------------------------------------------


def render_indigo(mol, options, frmt, margin, size, colors, ignoreCoords):

    renderer = indigo_renderer.IndigoRenderer(indigoObj)
    if options and hasattr(options, 'bgColor') and options.bgColor:
        indigoObj.setOption("render-background-color", "%s, %s, %s" % options.bgColor)
    indigoObj.setOption("render-output-format", frmt)
    indigoObj.setOption("render-margins", margin, margin)
    indigoObj.setOption("render-image-size", size, size)
    indigoObj.setOption("render-coloring", colors)
    indigoObj.setOption("ignore-stereochemistry-errors", "true")
    if ignoreCoords:
        mol.layout()
    image = renderer.renderToBuffer(mol)
    return image.tostring()

# ----------------------------------------------------------------------------------------------------------------------


def render_rdkit(mol, highlight, options, frmt, size, colors, ignoreCoords):

    leg = mol.GetProp("_Name") if mol.HasProp("_Name") else None
    matching = []
    if highlight:
        matching = highlight
    if ignoreCoords:
        AllChem.Compute2DCoords(mol)

    if NEW_RENDER_ENGINE:
        return render_rdkit_modern_rendering(mol, matching, options, frmt, size, colors, leg)
    else:
        return render_rdkit_legacy(mol, matching, options, frmt, size, colors, leg)

# ----------------------------------------------------------------------------------------------------------------------


def render_rdkit_modern_rendering(mol, highlight, options, frmt, size, colors, legend):

    if frmt == 'png':
        drawer = rdMolDraw2D.MolDraw2DCairo(size, size)
    elif frmt == 'svg':
        drawer = rdMolDraw2D.MolDraw2DSVG(size, size)
    else:
        return
    opts = drawer.drawOptions()
    if hasattr(options, 'bgColor') and options.bgColor:
        opts.setBackgroundColour(options.bgColor)
    else:
        opts.clearBackground = False

    if not colors:
        opts.useBWAtomPalette()
    else:
        opts.useDefaultAtomPalette()

    Chem.GetSSSR(mol)

    drawer.DrawMolecule(mol, highlightAtoms=highlight, legend=legend)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()

# ----------------------------------------------------------------------------------------------------------------------


def render_rdkit_legacy(mol, highlight, options, frmt, size, colors, legend):

    if not colors:
        dd = defaultdict(lambda: (0, 0, 0))
        options.elemDict = dd
    else:
        options.elemDict = STANDARD_RDKIT_COLORS

    if frmt == 'png':
        buf = StringIO.StringIO()
        image = draw.MolToImage(mol, size=(size, size), legend=legend, fitImage=True, options=options,
                                highlightAtoms=highlight)
        image.save(buf, "PNG")
        return buf.getvalue()

    elif frmt == 'svg':
        if cffi and cairocffi.version <= (1, 10, 0):
            imageData = io.BytesIO()
        else:
            imageData = StringIO.StringIO()
        surf = cairo.SVGSurface(imageData, size, size)
        ctx = cairo.Context(surf)
        canv = cairoCanvas.Canvas(ctx=ctx, size=(size, size), imageType='svg')
        draw.MolToImage(mol, size=(size, size), legend=legend, canvas=canv, fitImage=True, options=options,
                        highlightAtoms=highlight)
        canv.flush()
        surf.finish()
        return imageData.getvalue()

# ----------------------------------------------------------------------------------------------------------------------


def highlight_substructure_rdkit(molstring, smarts):
    mol = Chem.MolFromMolBlock(str(molstring), sanitize=True)
    if not mol:
        return
    mol.UpdatePropertyCache(strict=False)
    patt = Chem.MolFromSmarts(str(smarts))
    if not patt:
        return
    Chem.GetSSSR(patt)
    Chem.GetSSSR(mol)
    match = mol.HasSubstructMatch(patt)
    if not match:
        return
    matching = mol.GetSubstructMatch(patt)
    return mol, matching

# ----------------------------------------------------------------------------------------------------------------------


def highlight_substructure_indigo(molstring, smarts):

    try:
        mol = indigoObj.loadMolecule(str(molstring))
        patt = indigoObj.loadSmarts(str(smarts))
        match = indigoObj.substructureMatcher(mol).match(patt)
    except IndigoException:
        return
    if not match:
        return
    return match.highlightedTarget()

# ----------------------------------------------------------------------------------------------------------------------


def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# ----------------------------------------------------------------------------------------------------------------------


def list_flatten(l, a=None):
    if a is None:
        a = []
    for i in l:
        if isinstance(i, list):
            list_flatten(i, a)
        else:
            a.append(i)
    return a

# ----------------------------------------------------------------------------------------------------------------------


def unpack_request_params(params):
    ret = []
    for x in params:
        first, second = x
        if type(second) == list and len(second) == 1 and isinstance(second[0], basestring):
            ret.append((first, second[0]))
        else:
            ret.append(x)
    return ret

# ----------------------------------------------------------------------------------------------------------------------