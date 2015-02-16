from tastypie.test import ResourceTestCase
from chembl_webservices import api_name
from chembl_webservices.resources import *

URL_PREFIX = '/chembl_webservices/'
BASE_URL = URL_PREFIX + api_name + '/'

#-----------------------------------------------------------------------------------------------------------------------

class ActivityResourceTest(ResourceTestCase):

    def setUp(self):
        super(ActivityResourceTest, self).setUp()
        self.resource_class = ActivityResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class AssayResourceTest(ResourceTestCase):

    def setUp(self):
        super(AssayResourceTest, self).setUp()
        self.resource_class = AssayResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.chembl_id
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.chembl_id, second.chembl_id)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class AtcResourceTest(ResourceTestCase):

    def setUp(self):
        super(AtcResourceTest, self).setUp()
        self.resource_class = AtcResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class BindingSiteResourceTest(ResourceTestCase):

    def setUp(self):
        super(BindingSiteResourceTest, self).setUp()
        self.resource_class = BindingSiteResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class BiotherapeuticComponentsResourceTest(ResourceTestCase):

    def setUp(self):
        super(BiotherapeuticComponentsResourceTest, self).setUp()
        self.resource_class = BiotherapeuticComponentsResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class CellLineResourceTest(ResourceTestCase):

    def setUp(self):
        super(CellLineResourceTest, self).setUp()
        self.resource_class = CellLineResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class DocsResourceTest(ResourceTestCase):

    def setUp(self):
        super(DocsResourceTest, self).setUp()
        self.resource_class = DocsResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.chembl_id
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.chembl_id, second.chembl_id)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class ImageResourceTest(ResourceTestCase):

    def setUp(self):
        super(ImageResourceTest, self).setUp()
        self.resource_class = ImageResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.molecule.chembl_id

    def test_get_image_json(self):
        resp = self.api_client.get(self.detail_url + '.json', format='json')
        self.assertValidJSONResponse(resp)

    def test_get_image_svg(self):
        resp = self.api_client.get(self.detail_url + '.svg', format='svg')
        self.assertHttpOK(resp)
        self.assertTrue(resp['Content-Type'].startswith('image/svg+xml'))

    def test_get_detail_png(self):
        resp = self.api_client.get(self.detail_url + '.png', format='png')
        self.assertHttpOK(resp)

#-----------------------------------------------------------------------------------------------------------------------

class MechanismResourceTest(ResourceTestCase):

    def setUp(self):
        super(MechanismResourceTest, self).setUp()
        self.resource_class = MechanismResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeResourceTest(ResourceTestCase):

    def setUp(self):
        super(MoleculeResourceTest, self).setUp()
        self.resource_class = MoleculeResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.chembl_id
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.chembl_id, second.chembl_id)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class MoleculeFormsResourceTest(ResourceTestCase):

    def setUp(self):
        super(MoleculeFormsResourceTest, self).setUp()
        self.resource_class = MoleculeFormsResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.molecule.chembl_id
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.molecule.chembl_id, second.molecule.chembl_id)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class ProteinClassResourceTest(ResourceTestCase):

    def setUp(self):
        super(ProteinClassResourceTest, self).setUp()
        self.resource_class = ProteinClassResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class SimilarityResourceTest(ResourceTestCase):

    def setUp(self):
        super(SimilarityResourceTest, self).setUp()
        self.resource_class = SimilarityResource
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s/%s' % ('COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 70)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class SourceResourceTest(ResourceTestCase):

    def setUp(self):
        super(SourceResourceTest, self).setUp()
        self.resource_class = SourceResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class StatusResourceTest(ResourceTestCase):

    def setUp(self):
        super(StatusResourceTest, self).setUp()
        self.resource_class = StatusResource
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class SubstructureResourceTest(ResourceTestCase):

    def setUp(self):
        super(SubstructureResourceTest, self).setUp()
        self.resource_class = SubstructureResource
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % 'CN(CCCN)c1cccc2ccccc12'

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class TargetResourceTest(ResourceTestCase):

    def setUp(self):
        super(TargetResourceTest, self).setUp()
        self.resource_class = TargetResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.chembl_id
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.chembl_id, second.chembl_id)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

class TargetComponentsResourceTest(ResourceTestCase):

    def setUp(self):
        super(TargetComponentsResourceTest, self).setUp()
        self.resource_class = TargetComponentsResource
        first_two = self.resource_class._meta.queryset._clone()[0:2]
        first = first_two[0]
        second = first_two[1]
        self.resource_url = BASE_URL + self.resource_class._meta.resource_name
        self.detail_url = self.resource_url + '/%s' % first.pk
        self.multiple_url = self.resource_url + '/set/%s;%s' % (first.pk, second.pk)

    def test_get_list_json(self):
        resp = self.api_client.get(self.resource_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_list_xml(self):
        resp = self.api_client.get(self.resource_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_detail_json(self):
        resp = self.api_client.get(self.detail_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_detail_xml(self):
        resp = self.api_client.get(self.detail_url, format='xml')
        self.assertValidXMLResponse(resp)

    def test_get_multiple_json(self):
        resp = self.api_client.get(self.multiple_url, format='json')
        self.assertValidJSONResponse(resp)

    def test_get_multiple_xml(self):
        resp = self.api_client.get(self.multiple_url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------