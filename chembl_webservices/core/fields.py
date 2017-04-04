from tastypie.exceptions import ApiFieldError
from tastypie.fields import ApiField, NOT_PROVIDED
from django.utils import six

# ----------------------------------------------------------------------------------------------------------------------


def dehydrate(self, bundle, for_list=True):
    """
    Takes data from the provided object and prepares it for the
    resource.
    """
    if self.attribute is not None:
        # Check for `__` in the field for looking through the relation.
        current_object = bundle.obj

        for attr in self._attrs:
            previous_object = current_object
            try:
                current_object = getattr(current_object, attr, None)
            except:
                current_object = None

            if current_object is None:
                if self.has_default():
                    current_object = self._default
                    # Fall out of the loop, given any further attempts at
                    # accesses will fail miserably.
                    break
                elif self.null:
                    current_object = None
                    # Fall out of the loop, given any further attempts at
                    # accesses will fail miserably.
                    break
                else:
                    raise ApiFieldError("The object '%r' has an empty attribute '%s' and doesn't allow a default or null value." % (previous_object, attr))

        if callable(current_object):
            current_object = current_object()

        return self.convert(current_object)

    if self.has_default():
        return self.convert(self.default)
    else:
        return None

# ----------------------------------------------------------------------------------------------------------------------


def __init__(self, attribute=None, default=NOT_PROVIDED, null=False, blank=False, readonly=False, unique=False,
             help_text=None, use_in='all', verbose_name=None):
        """
        Sets up the field. This is generally called when the containing
        ``Resource`` is initialized.

        Optionally accepts an ``attribute``, which should be a string of
        either an instance attribute or callable off the object during the
        ``dehydrate`` or push data onto an object during the ``hydrate``.
        Defaults to ``None``, meaning data will be manually accessed.

        Optionally accepts a ``default``, which provides default data when the
        object being ``dehydrated``/``hydrated`` has no data on the field.
        Defaults to ``NOT_PROVIDED``.

        Optionally accepts a ``null``, which indicated whether or not a
        ``None`` is allowable data on the field. Defaults to ``False``.

        Optionally accepts a ``blank``, which indicated whether or not
        data may be omitted on the field. Defaults to ``False``.

        Optionally accepts a ``readonly``, which indicates whether the field
        is used during the ``hydrate`` or not. Defaults to ``False``.

        Optionally accepts a ``unique``, which indicates if the field is a
        unique identifier for the object.

        Optionally accepts ``help_text``, which lets you provide a
        human-readable description of the field exposed at the schema level.
        Defaults to the per-Field definition.

        Optionally accepts ``use_in``. This may be one of ``list``, ``detail``
        ``all`` or a callable which accepts a ``bundle`` and returns
        ``True`` or ``False``. Indicates wheather this field will be included
        during dehydration of a list of objects or a single object. If ``use_in``
        is a callable, and returns ``True``, the field will be included during
        dehydration.
        Defaults to ``all``.
        """
        # Track what the index thinks this field is called.

        self.instance_name = None
        self._resource = None
        self.attribute = attribute
        # Check for `__` in the field for looking through the relation.
        self._attrs = attribute.split('__') if attribute is not None and isinstance(attribute, six.string_types) else []
        self._default = default
        self.null = null
        self.blank = blank
        self.readonly = readonly
        self.value = None
        self.unique = unique
        self.use_in = 'all'

        if use_in in ['all', 'detail', 'list', 'search'] or callable(use_in):
            self.use_in = use_in

        self.verbose_name = verbose_name

        if help_text:
            self.help_text = help_text

# ----------------------------------------------------------------------------------------------------------------------


def monkeypatch_tastypie_field():
    ApiField.dehydrate = dehydrate
    ApiField.__init__ = __init__

# ----------------------------------------------------------------------------------------------------------------------
