from tastypie.exceptions import ApiFieldError
from tastypie.fields import ApiField

def dehydrate(self, bundle, for_list=True):
    """
    Takes data from the provided object and prepares it for the
    resource.
    """
    if self.attribute is not None:
        # Check for `__` in the field for looking through the relation.
        attrs = self.attribute.split('__')
        current_object = bundle.obj

        for attr in attrs:
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

def monkeypatch_tastypie_field():
    ApiField.dehydrate = dehydrate