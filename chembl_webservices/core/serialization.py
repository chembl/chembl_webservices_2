__author__ = 'mnowotka'

from tastypie.serializers import Serializer
from tastypie.exceptions import UnsupportedFormat
from tastypie.bundle import Bundle
from simplejson import JSONDecodeError
from tastypie.exceptions import BadRequest
import urlparse
import logging

try:
    import defusedxml.lxml as lxml
    from defusedxml.common import DefusedXmlException
    from defusedxml.lxml import parse as parse_xml
    from lxml.etree import Element, tostring, LxmlError, XMLParser
except ImportError:
    lxml = None


#-----------------------------------------------------------------------------------------------------------------------

def valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF or
        codepoint in (0x9, 0xA, 0xD) or
        0xE000 <= codepoint <= 0xFFFD or
        0x10000 <= codepoint <= 0x10FFFF
        )

#-----------------------------------------------------------------------------------------------------------------------

class ChEMBLApiSerializer(Serializer):

    formats = ['xml', 'json', 'jsonp', 'yaml']

    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'urlencode': 'application/x-www-form-urlencoded',
    }

    def __init__(self, name=None, names=None):
        self.objName = name
        self.objNames = names
        self.log = logging.getLogger(__name__)
        super(ChEMBLApiSerializer, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def get_mime_for_format(self, format):
        """
        Given a format, attempts to determine the correct MIME type.

        If not available on the current ``Serializer``, returns
        ``application/json`` by default.
        """
        try:
            return self.content_types[format]
        except KeyError:
            return ''

#-----------------------------------------------------------------------------------------------------------------------

    def deserialize(self, content, format='application/json', tag=None):
        """
        Given some data and a format, calls the correct method to deserialize
        the data and returns the result.
        """
        desired_format = None

        format = format.split(';')[0]

        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "from_%s" % short_format):
                    desired_format = short_format
                    break

        if desired_format is None:
            raise UnsupportedFormat(
                "The format indicated '%s' had no available deserialization method. Please check your ``formats`` "
                "and ``content_types`` on your Serializer." % format)

        if desired_format == 'xml' and tag:
            deserialized = getattr(self, "from_%s" % desired_format)(content, tag)
        else:
            try:
                deserialized = getattr(self, "from_%s" % desired_format)(content)
            except (JSONDecodeError, ValueError):
                raise BadRequest('%s is not serialised using %s format' % (content, desired_format))
        return deserialized

#-----------------------------------------------------------------------------------------------------------------------

    def from_urlencode(self, data, options=None):

        qs = dict((k, v if len(v) > 1 else v[0] )
                  for k, v in urlparse.parse_qs(data).iteritems())
        return qs

#-----------------------------------------------------------------------------------------------------------------------

    def to_urlencode(self, content):
        pass

#-----------------------------------------------------------------------------------------------------------------------

    def to_etree(self, data, options=None, name=None, depth=0):
        """
        Given some data, converts that data to an ``etree.Element`` suitable
        for use in the XML output.
        """

        if isinstance(data, (list, tuple)):
            new_name = None
            if name:
                element = Element(name)
                new_name = self.objNames.get(name) if self.objNames else name
            else:
                element = Element('objects')
            for item in data:
                element.append(self.to_etree(item, options, name=new_name, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif isinstance(data, dict):
            if depth == 0:
                element = Element(name or 'response')
            else:
                element = Element(name or self.objName)
            for (key, value) in data.items():
                element.append(self.to_etree(value, options, name=key, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif isinstance(data, Bundle):
            element = Element(name or self.objName)
            for field_name, field_object in data.data.items():
                element.append(self.to_etree(field_object, options, name=field_name, depth=depth+1))
                element[:] = sorted(element, key=lambda x: x.tag)
        elif hasattr(data, 'dehydrated_type'):
            if getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == False:
                if data.full:
                    return self.to_etree(data.fk_resource, options, name, depth+1)
                else:
                    return self.to_etree(data.value, options, name, depth+1)
            elif getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == True:
                if data.full:
                    element = Element(name or 'objects')
                    for bundle in data.m2m_bundles:
                        element.append(self.to_etree(bundle, options, bundle.resource_name, depth+1))
                else:
                    element = Element(name or 'objects')
                    for value in data.value:
                        element.append(self.to_etree(value, options, name, depth=depth+1))
            else:
                return self.to_etree(data.value, options, name)
        else:
            element = Element(name or 'value')
            simple_data = self.to_simple(data, options)
            if simple_data:
                try:
                    element.text = unicode(simple_data)
                except ValueError as e:
                    self.log.error('Not valid XML character detected in ', exc_info=True,
                        extra={'data': simple_data, 'original_exception': e})
                    cleaned_string = ''.join(c for c in simple_data if valid_xml_char_ordinal(c))
                    element.text = unicode(cleaned_string)

        return element

#-----------------------------------------------------------------------------------------------------------------------
