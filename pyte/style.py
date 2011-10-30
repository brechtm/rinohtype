

class ParentStyleException(Exception):
    pass


class ParentStyleType(type):
    def __getattr__(cls, key):
        raise ParentStyleException

    def __repr__(cls):
        return cls.__name__


class ParentStyle(object, metaclass=ParentStyleType):
    pass


class Style(object):
    attributes = {}

    def __init__(self, name, base=ParentStyle, **attributes):
        self.name = name
        self.base = base
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        self.__dict__.update(attributes)

    def __repr__(self):
        return '{0}({1}) > {2}'.format(self.__class__.__name__ , self.name,
                                       self.base)

        return self.get_default(name)

    def __getattr__(self, name):
        if self.base == None:
            return self._get_default(name)
        else:
            return getattr(self.base, name)

    def _get_default(self, name):
        for cls in self.__class__.__mro__:
            try:
                return cls.attributes[name]
            except (KeyError, AttributeError):
                pass
        raise AttributeError("No attribute '{}' in {}".format(name, self))

    def _supported_attributes(self):
        attributes = {}
        for cls in reversed(self.__class__.__mro__):
            try:
                attributes.update(cls.attributes)
            except AttributeError:
                pass
        return attributes
