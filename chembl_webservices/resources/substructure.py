__author__ = 'mnowotka'

from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from django.conf.urls import url
from django.core.urlresolvers import NoReverseMatch
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from chembl_webservices.resources.molecule import MoleculeResource
import itertools
from django.conf import settings

try:
    from chembl_compatibility.models import CompoundMols
except ImportError:
    from chembl_core_model.models import CompoundMols

try:
    from chembl_compatibility.models import MoleculeDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary

try:
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeHierarchy

from chembl_webservices.core.fields import monkeypatch_tastypie_field
monkeypatch_tastypie_field()

minimal_substructure_length = 5

# ----------------------------------------------------------------------------------------------------------------------


class SubstructureResource(MoleculeResource):

    class Meta(MoleculeResource.Meta):
        queryset = MoleculeDictionary.objects.all()
        resource_name = 'substructure'

# ----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):

        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/schema\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/datatables\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('get_datatables'), name="api_get_datatables"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<chembl_id>[Cc][Hh][Ee][Mm][Bb][Ll]\d[\d]*)\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<standard_inchi_key>[A-Z]{14}-[A-Z]{10}-[A-Z])\.(?P<format>\w+)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<smiles>[^jx]+)\.(?P<format>json|xml|sdf|mol)$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<smiles>[^jx]+)%s$" % (self._meta.resource_name, trailing_slash(),), self.wrap_view('dispatch_list'), name="api_dispatch_detail"),
        ]

# ----------------------------------------------------------------------------------------------------------------------

    def prepend_urls(self):
        return []

# ----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, bundle, **kwargs):
        smiles = kwargs.pop('smiles', None)
        std_inchi_key = kwargs.pop('standard_inchi_key', None)
        chembl_id = kwargs.pop('chembl_id', None)

        if not smiles and not std_inchi_key and not chembl_id:
            raise BadRequest("Structure or identifier required.")

        if not smiles:
            try:
                if chembl_id:
                    mol_filters = {'chembl_id': chembl_id}
                else:
                    mol_filters = {'compoundstructures__standard_inchi_key': std_inchi_key}
                objects = self.apply_filters(bundle.request, mol_filters).values_list(
                    'compoundstructures__canonical_smiles', flat=True)
                stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in mol_filters.items()])
                length = len(objects)
                if length <= 0:
                    raise ObjectDoesNotExist("Couldn't find an instance of '%s' which matched '%s'." %
                                             (self._meta.object_class.__name__, stringified_kwargs))
                elif length > 1:
                    raise MultipleObjectsReturned("More than '%s' matched '%s'." % (self._meta.object_class.__name__,
                                                                                    stringified_kwargs))
                smiles = objects[0]
                if not smiles:
                    raise ObjectDoesNotExist(
                        "No chemical structure defined for identifier {0}".format(chembl_id or std_inchi_key))
            except TypeError as e:
                if e.message.startswith('Related Field has invalid lookup:'):
                    raise BadRequest(e.message)
                else:
                    raise e
            except ValueError:
                raise BadRequest("Invalid resource lookup data provided (mismatched type).")

        if not isinstance(smiles, basestring):
            raise BadRequest("Substructure can only handle a single chemical query identified by SMILES, "
                             "InChiKey or ChEMBL ID.")

        elif len(smiles) < minimal_substructure_length:
            raise BadRequest("Structure %s is too short. Minimal structure length is %s" % (smiles, minimal_substructure_length))

        mols = CompoundMols.objects.with_substructure(smiles).defer('molfile').values_list('molecule_id', flat=True)

        filters = {
            'chembl__entity_type': 'COMPOUND',
            'compoundstructures__isnull': False,
            'pk__in': MoleculeHierarchy.objects.all().values_list('parent_molecule_id'),
            'compoundproperties__isnull': False,
        }

        standard_filters, distinct = self.build_filters(filters=kwargs)

        filters.update(standard_filters)
        try:
            objects = self.get_object_list(bundle.request).filter(**filters).filter(pk__in=mols)
        except TypeError as e:
            if e.message.startswith('Related Field has invalid lookup:'):
                raise BadRequest(e.message)
            else:
                raise e
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided (mismatched type).")
        if distinct:
            objects = objects.distinct()
        return self.authorized_read_list(objects, bundle)

# ----------------------------------------------------------------------------------------------------------------------

    def get_resource_uri(self, bundle_or_obj=None, url_name='dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'dispatch_detail'

        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

# ----------------------------------------------------------------------------------------------------------------------

    def remove_api_resource_names(self, kwargs):
        return super(MoleculeResource, self).remove_api_resource_names(self.decode_plus(kwargs))

# ----------------------------------------------------------------------------------------------------------------------

    def generate_cache_key(self, *args, **kwargs):
        smooshed = []

        identifier = kwargs.get('smiles') or kwargs.get('standard_inchi_key') or kwargs.get('chembl_id')
        if not identifier:
            raise BadRequest("Structure or identifier required.")

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
        cache_key = "%s:%s:%s:%s:%s:%s:%s:%s" % (self._meta.api_name,
                                                 self._meta.resource_name,
                                                 '|'.join(args),
                                                 str(identifier),
                                                 str(limit),
                                                 str(offset),
                                                 '|'.join(order_bits),
                                                 '|'.join(sorted(smooshed)))
        return cache_key

# ----------------------------------------------------------------------------------------------------------------------
