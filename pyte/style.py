"""
Base classes and exceptions for styles of document elements.

* :class:`Style`: Dictionary storing a set of style attributes
* :class:`Styled`: A styled entity, having a :class:`Style` associated with it
* :class:`StyleStore`: Dictionary storing a set of related `Style`s by name
* :const:`PARENT_STYLE`: Special style that forwards style lookups to the parent
                        :class:`Styled`
* :exc:`ParentStyleException`: Thrown when style attribute lookup needs to be
                               delegated to the parent :class:`Styled`
"""


from .document import DocumentElement


__all__ = ['Style', 'Styled', 'StyleStore',
           'PARENT_STYLE', 'ParentStyleException']


class ParentStyleException(Exception):
    """Style attribute not found. Consult the parent :class:`Styled`."""


class DefaultValueException(Exception):
    """The attribute is not specified in this :class:`Style` or any of its base
    styles. Return the default value for the attribute."""


class Style(dict):
    """"Dictionary storing style attributes.

    Attrributes can also be accessed as attributes."""

    attributes = {}
    """Dictionary holding the supported style attributes for this :class:`Style`
    class (keys) and their default values (values)"""

    def __init__(self, base=None, **attributes):
        """Style attributes are as passed as keyword arguments. Supported
        attributes include those defined in the :attr:`attributes` attribute of
        this style class and those defined in style classes this one inherits
        from.

        Optionally, a `base` (:class:`Style`) is passed, where attributes are
        looked up when they have not been specified in this style.
        Alternatively, if `base` is :class:`PARENT_STYLE`, the attribute lookup
        is forwarded to the parent of the element the lookup originates from.
        If `base` is a :class:`str`, it is used to look up the base style in
        the :class:`StyleStore` this style is stored in."""
        self.base = base
        self.name = None
        self.store = None
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        super().__init__(attributes)

    @property
    def base(self):
        """Return the base style for this style."""
        if isinstance(self._base, str):
            return self.store[self._base]
        else:
            return self._base

    @base.setter
    def base(self, base):
        """Set this style's base to `base`"""
        self._base = base

    def __repr__(self):
        """Return a textual representation of this style."""
        return '{0}({1}) > {2}'.format(self.__class__.__name__, self.name or '',
                                       self.base)

    def __copy__(self):
        copy = self.__class__(base=self.base, **self)
        if self.name is not None:
            copy.name = self.name + ' (copy)'
            copy.store = self.store
        return copy

    def __getattr__(self, attribute):
        return self[attribute]

    def __getitem__(self, attribute):
        """Return the value of `attribute`.

        If the attribute is not specified in this :class:`Style`, find it in
        this style's base styles (hierarchically), or ultimately return the
        default value for `attribute`."""
        try:
            return self._recursive_get(attribute)
        except DefaultValueException:
            return self._get_default(attribute)

    def _recursive_get(self, attribute):
        """Recursively search for the value of `attribute`.

        If the attribute is not specified in this style, defer the lookup to the
        base style. When the attribute is specified nowhere in the chain of base
        styles, raise a :class:`DefaultValueException`.
        """
        try:
            return super().__getitem__(attribute)
        except KeyError:
            if self.base is None:
                raise DefaultValueException
            return self.base._recursive_get(attribute)

    def _get_default(self, attribute):
        """Return the default value for `attribute`.

        If no default is specified in this style, get the default from the
        nearest superclass.
        If `attribute` is not supported, raise a :class:`KeyError`."""
        try:
            for cls in self.__class__.__mro__:
                if attribute in cls.attributes:
                    return cls.attributes[attribute]
        except AttributeError:
            raise KeyError("No attribute '{}' in {}".format(attribute, self))

    def _supported_attributes(self):
        """Return a :class:`dict` of the attributes supported by this style
        class."""
        attributes = {}
        for cls in reversed(self.__class__.__mro__):
            try:
                attributes.update(cls.attributes)
            except AttributeError:
                pass
        return attributes


class ParentStyle(object):
    """Special style that delegates attribute lookups by raising a
    :class:`ParentStyleException` on each attempt to access an attribute."""

    def __repr__(self):
        return self.__class__.__name__

    def __getattr__(self, attribute):
        raise ParentStyleException

    def __getitem__(self, attribute):
        raise ParentStyleException


PARENT_STYLE = ParentStyle()
"""Special style that forwards style lookups to the parent of the
:class:`Styled` from which the lookup originates."""


class Styled(DocumentElement):
    """An element that has a :class:`Style` associated with it."""

    style_class = None
    """The :class:`Style` subclass that corresponds to this :class:`Styled`
    subclass."""

    def __init__(self, style=None, parent=None):
        """Associates `style` with this element. If `style` is `None`, an empty
        :class:`Style` is create, effectively using the defaults defined for the
        associated :class:`Style` class).
        A `parent` can be passed on object initialization, or later by
        assignment to the `parent` attribute."""
        super().__init__(parent=parent)
        if style is None:
            style = self.style_class()
        if style != PARENT_STYLE and not isinstance(style, self.style_class):
            raise TypeError('the style passed to {0} should be of type {1}'
                            .format(self.__class__.__name__,
                                    self.style_class.__name__))
        self.style = style
        self.cached_style = {}

    def get_style(self, attribute):
        """Return `attribute` of the associated :class:`Style`.

        If this element's :class:`Style` or one of its bases is `PARENT_STYLE`,
        the style attribute is fetched from this element's parent."""
        try:
            return self.cached_style[attribute]
        except KeyError:
            try:
                value = self.style[attribute]
            except ParentStyleException:
                value = self.parent.get_style(attribute)
            self.cached_style[attribute] = value
            return value


class StyleStore(dict):
    """Dictionary storing a set of related :class:`Style`s by name.

    :class:`Style`s stored in a :class:`StyleStore` can refer to their base
    style by name. See :class:`Style`."""

    def __setitem__(self, key, value):
        value.name = key
        value.store = self
        super().__setitem__(key, value)
