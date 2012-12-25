
from .document import DocumentElement


class ParentStyleException(Exception):
    pass


class ParentStyleType(type):
    def __repr__(cls):
        return cls.__name__

    def __getattr__(cls, key):
        raise ParentStyleException

    def __getitem__(cls, key):
        raise ParentStyleException

    def _recursive_get(cls, key):
        raise ParentStyleException


class ParentStyle(object, metaclass=ParentStyleType):
    pass


class DefaultValueException(Exception):
    pass


class Style(dict):
    attributes = {}

    def __init__(self, base=ParentStyle, **attributes):
        self.base = base
        self.name = None
        self.store = None
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        self.update(attributes)

    @property
    def base(self):
        if isinstance(self._base, str):
            return self.store[self._base]
        else:
            return self._base

    @base.setter
    def base(self, base):
        self._base = base

    def __repr__(self):
        return '{0}({1}) > {2}'.format(self.__class__.__name__, self.name,
                                       self.base)

    def __copy__(self):
        copy = self.__class__(base=self.base, **self)
        if self.name is not None:
            copy.name = self.name + ' (copy)'
            copy.store = self.store
        return copy

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        try:
            return self._recursive_get(key)
        except DefaultValueException:
            return self._get_default(key)

    def _recursive_get(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if self.base is None:
                raise DefaultValueException
            return self.base._recursive_get(key)

    def _get_default(self, key):
        for cls in self.__class__.__mro__:
            if key in cls.attributes:
                return cls.attributes[key]
        raise KeyError("No attribute '{}' in {}".format(key, self))

    def _supported_attributes(self):
        attributes = {}
        for cls in reversed(self.__class__.__mro__):
            try:
                attributes.update(cls.attributes)
            except AttributeError:
                pass
        return attributes


class Styled(DocumentElement):
    style_class = None

    def __init__(self, style=None):
        super().__init__()
        if style is None:
            style = self.style_class()
        if style != ParentStyle and not isinstance(style, self.style_class):
            raise TypeError('the style passed to {0} should be of type {1}'
                            .format(self.__class__.__name__,
                                    self.style_class.__name__))
        self.style = style
        self.cached_style = {}

    def get_style(self, attribute):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        value.name = key
        value.store = self
        super().__setitem__(key, value)
