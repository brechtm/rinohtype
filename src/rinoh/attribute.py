# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import OrderedDict
from types import FunctionType

from .util import NamedDescriptor, WithNamedDescriptors


__all__ = ['AttributeType', 'AcceptNoneAttributeType', 'OptionSet', 'Attribute',
           'OverrideDefault', 'AttributesDictionary', 'Bool', 'Integer', 'Var']


class AttributeType(object):
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    @classmethod
    def check_type(cls, value):
        return isinstance(value, cls)

    @classmethod
    def from_string(cls, string):
        return cls.parse_string(string)

    @classmethod
    def parse_string(cls, string):
        raise NotImplementedError


class AcceptNoneAttributeType(AttributeType):
    @classmethod
    def check_type(cls, value):
        return (isinstance(value, type(None))
                or super(__class__, cls).check_type(value))

    @classmethod
    def from_string(cls, string):
        if string.strip().lower() == 'none':
            return None
        return super(__class__, cls).from_string(string)


class OptionSetMeta(type):
    def __new__(cls, classname, bases, cls_dict):
        cls_dict['__doc__'] = (cls_dict['__doc__'] + '\n\n'
                               if '__doc__' in cls_dict else '')
        cls_dict['__doc__'] += ('Accepts these options:\n\n'
                               + '\n'.join("- '{}'".format(val)
                                           for val in cls_dict['values']))
        return super().__new__(cls, classname, bases, cls_dict)


class OptionSet(AttributeType, metaclass=OptionSetMeta):
    """Accepts the values listed in :attr:`values`"""

    values = ()

    @classmethod
    def check_type(cls, value):
        return value in cls.values

    @classmethod
    def parse_string(cls, string):
        value_strings = ['none' if value is None else value.lower()
                         for value in cls.values]
        try:
            index = value_strings.index(string.lower())
        except ValueError:
            raise ValueError("'{}' is not a valid {}. Must be one of: '{}'"
                             .format(string, cls.__name__,
                                     "', '".join(value_strings)))
        return cls.values[index]


class Attribute(NamedDescriptor):
    """Descriptor used to describe a style attribute"""
    def __init__(self, accepted_type, default_value, description, name=None):
        self.accepted_type = accepted_type
        self.default_value = default_value
        self.description = description
        self.name = name

    def __get__(self, style, type=None):
        try:
            return style.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, style, value):
        if not self.accepted_type.check_type(value):
            raise TypeError('The {} attribute only accepts {} instances'
                            .format(self.name, self.accepted_type))
        style[self.name] = value


class OverrideDefault(Attribute):
    """Overrides the default value of an attribute defined in a superclass"""
    def __init__(self, default_value):
        self.default_value = default_value
        self.overrides = None

    @property
    def accepted_type(self):
        return self.overrides.accepted_type

    @property
    def description(self):
        return self.overrides.description


class WithAttributes(WithNamedDescriptors):
    @classmethod
    def __prepare__(metacls, name, bases):
        return OrderedDict()  # keeps the order of member variables (PEP3115)

    def __new__(mcls, classname, bases, cls_dict):
        attributes = cls_dict['_attributes'] = OrderedDict()
        doc = ''
        for name, attr in cls_dict.items():
            if isinstance(attr, Attribute):
                attributes[name] = attr
                if isinstance(attr, OverrideDefault):
                    for base_cls in bases:
                        try:
                            attr.overrides = base_cls.attribute_definition(
                                name)
                            break
                        except KeyError:
                            pass
                    else:
                        raise NotImplementedError
                    doc += ('    {}: Overrides :class:`{}` default: {}\n'
                            .format(name, base_cls.__name__,
                                    attr.default_value))
                else:
                    doc += ('    {} ({}): {}. Default: {}\n'
                           .format(name, attr.accepted_type.__name__,
                                   attr.description, attr.default_value))
        supported_attributes = set(name for name in attributes)
        if attributes:
            doc = 'Args:\n' + doc
        mro_clss = []
        for base_class in bases:
            try:
                supported_attributes.update(base_class._supported_attributes)
                for mro_class in base_class.__mro__:
                    if getattr(mro_class, '_attributes', None):
                        mro_doc = ('* :class:`.{}`: {}'
                                   .format(mro_class.__name__,
                                           ', '.join('**{}**'.format(name)
                                                     for name
                                                     in mro_class._attributes)
                                           ))
                        mro_clss.append(mro_doc)
            except AttributeError:
                pass
        cls_dict['_supported_attributes'] = supported_attributes
        if mro_clss:
            doc += '\n:Inherited parameters: '
            doc += ('\n                       ').join(mro_clss)
        cls_dict['__doc__'] = (cls_dict['__doc__'] + '\n\n'
                               if '__doc__' in cls_dict else '\n') + doc
        return super().__new__(mcls, classname, bases, cls_dict)


class AttributesDictionary(OrderedDict, metaclass=WithAttributes):
    default_base = None

    def __init__(self, base=None, **attributes):
        self.base = base or self.default_base
        for name, value in attributes.items():
            try:
                self._check_attribute_type(name, value, accept_variables=True)
            except KeyError:
                raise TypeError('{} is not a supported attribute for '
                                '{}'.format(name, type(self).__name__))
        super().__init__(attributes)

    def _check_attribute_type(self, name, value, accept_variables):
        attribute = self.attribute_definition(name)
        if isinstance(value, Var):
            if not accept_variables:
                raise TypeError("The '{}' attribute does not accept variables"
                                .format(name))
        elif not attribute.accepted_type.check_type(value):
            type_name = type(value).__name__
            raise TypeError("{} ({}) is not of the correct type for the '{}' "
                            "attribute".format(value, type_name, name))

    @classmethod
    def _get_default(cls, attribute):
        """Return the default value for `attribute`.

        If no default is specified in this style, get the default from the
        nearest superclass.
        If `attribute` is not supported, raise a :class:`KeyError`."""
        try:
            for klass in cls.__mro__:
                if attribute in klass._attributes:
                    return klass._attributes[attribute].default_value
        except AttributeError:
            raise KeyError("No attribute '{}' in {}".format(attribute, cls))

    @classmethod
    def attribute_definition(cls, name):
        try:
            for klass in cls.__mro__:
                if name in klass._attributes:
                    return klass._attributes[name]
        except AttributeError:
            pass
        raise KeyError

    def get_value(self, attribute, rule_set):
        value = self[attribute]
        if isinstance(value, Var):
            accepted_type = self.attribute_definition(attribute).accepted_type
            value = value.get(accepted_type, rule_set)
            self._check_attribute_type(attribute, value, accept_variables=False)
        return value


class RuleSet(OrderedDict):
    def __init__(self, base=None, **kwargs):
        super().__init__(**kwargs)
        self.base = base

    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            if self.base is not None:
                return self.base[name]
            raise

    def __setitem__(self, name, style):
        assert name not in self
        if isinstance(style, AttributesDictionary):
            style.name = name
        super().__setitem__(name, style)

    def __call__(self, name, **kwargs):
        self[name] = self.get_entry_class(name)(**kwargs)

    def __str__(self):
        return '{}({})'.format(type(self).__name__, self.name)

    def get_variable(self, name, accepted_type):
        try:
            return self._get_variable(name, accepted_type)
        except KeyError:
            return self.base.get_variable(name, accepted_type)

    def get_entry_class(self, name):
        raise NotImplementedError

    def _get_variable(self, name, accepted_type):
        raise NotImplementedError


class Bool(AttributeType):
    @classmethod
    def check_type(cls, value):
        return isinstance(value, bool)

    @classmethod
    def parse_string(cls, string):
        lower_string = string.lower()
        if lower_string not in ('true', 'false'):
            raise ValueError("'{}' is not a valid {}. Must be one of 'true' or "
                             "'false'".format(string, cls.__name__))
        return lower_string == 'true'


class Integer(AttributeType):
    @classmethod
    def check_type(cls, value):
        return isinstance(value, int)

    @classmethod
    def parse_string(cls, string):
        try:
            return int(string)
        except ValueError:
            raise ValueError("'{}' is not a valid {}"
                             .format(string, cls.__name__))


class Function(AttributeType):
    @classmethod
    def check_type(cls, value):
        return isinstance(value, (FunctionType, type(None)))


# variables

class Var(object):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def get(self, accepted_type, rule_set):
        return rule_set.get_variable(self.name, accepted_type)
