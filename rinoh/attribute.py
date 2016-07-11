# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from types import FunctionType

from .util import NamedDescriptor


__all__ = ['AttributeType', 'AcceptNoneAttributeType', 'OptionSet', 'Attribute',
           'OverrideDefault', 'Bool', 'Integer']


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


class OptionSet(AttributeType):
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
        if not isinstance(value, self.accepted_type):
            raise TypeError('The {} style attribute only accepts {} instances'
                            .format(self.name, self.accepted_type))
        style[self.name] = value

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)\n'
                ':default: {}'
                .format(self.description, self.accepted_type.__name__,
                        self.default_value))


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
