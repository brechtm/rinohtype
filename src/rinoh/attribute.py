# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from collections import OrderedDict
from configparser import ConfigParser
from itertools import chain
from warnings import warn

from .util import (NamedDescriptor, WithNamedDescriptors,
                   NotImplementedAttribute, class_property)


__all__ = ['AttributeType', 'AcceptNoneAttributeType', 'OptionSet', 'Attribute',
           'OverrideDefault', 'AttributesDictionary', 'RuleSet', 'RuleSetFile',
           'Bool', 'Integer', 'Var']


class AttributeType(object):
    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

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
        raise NotImplementedError(cls)

    RE_VARIABLE = re.compile(r'^\$\(([a-z_ -]+)\)$', re.IGNORECASE)

    @classmethod
    def validate(cls, value, accept_variables=False, attribute_name=None):
        if isinstance(value, str):
            stripped = value.replace('\n', ' ').strip()
            m = cls.RE_VARIABLE.match(stripped)
            if m:
                value = Var(m.group(1))
            else:
                value = cls.from_string(stripped)
        if isinstance(value, Var):
            if not accept_variables:
                raise TypeError("The '{}' attribute does not accept variables"
                                .format(attribute_name))
        elif not cls.check_type(value):
            raise TypeError("{} ({}) is not of the correct type for the '{}' "
                            "attribute".format(value, type(value).__name__,
                                               attribute_name))
        return value

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(value) if value else '(no value)'

    @classmethod
    def doc_format(cls):
        warn('Missing implementation for {}.doc_format'.format(cls.__name__))
        return ''


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

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format('none' if value is None else value)


class OptionSetMeta(type):
    def __new__(metacls, classname, bases, cls_dict):
        cls = super().__new__(metacls, classname, bases, cls_dict)
        cls.__doc__ = (cls_dict['__doc__'] + '\n\n'
                       if '__doc__' in cls_dict else '')
        cls.__doc__ += 'Accepts: {}'.format(cls.doc_format())
        return cls

    def __getattr__(cls, item):
        if item == 'NONE' and None in cls.values:
            return None
        string = item.lower().replace('_', ' ')
        if item.isupper() and string in cls.values:
            return string
        raise AttributeError(item)

    def __iter__(cls):
        return iter(cls.values)


class OptionSet(AttributeType, metaclass=OptionSetMeta):
    """Accepts the values listed in :attr:`values`"""

    values = ()

    @classmethod
    def check_type(cls, value):
        return value in cls.values

    @class_property
    def value_strings(cls):
        return ['none' if value is None else value.lower()
                for value in cls.values]

    @classmethod
    def parse_string(cls, string):
        try:
            index = cls.value_strings.index(string.lower())
        except ValueError:
            raise ValueError("'{}' is not a valid {}. Must be one of: '{}'"
                             .format(string, cls.__name__,
                                     "', '".join(cls.value_strings)))
        return cls.values[index]

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(value)

    @classmethod
    def doc_format(cls):
        return ', '.join('``{}``'.format(s) for s in cls.value_strings)


class Attribute(NamedDescriptor):
    """Descriptor used to describe a style attribute"""
    def __init__(self, accepted_type, default_value, description):
        self.name = None
        self.accepted_type = accepted_type
        self.default_value = accepted_type.validate(default_value)
        self.description = description

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
        self._default_value = default_value

    @property
    def overrides(self):
        return self._overrides

    @overrides.setter
    def overrides(self, attribute):
        self._overrides = attribute
        self.default_value = self.accepted_type.validate(self._default_value)

    @property
    def accepted_type(self):
        return self.overrides.accepted_type

    @property
    def description(self):
        return self.overrides.description


class WithAttributes(WithNamedDescriptors):
    def __new__(mcls, classname, bases, cls_dict):
        attributes = cls_dict['_attributes'] = OrderedDict()
        doc = []
        for name, attr in cls_dict.items():
            if not isinstance(attr, Attribute):
                continue
            attributes[name] = attr
            if isinstance(attr, OverrideDefault):
                for mro_cls in (cls for base_cls in bases
                                for cls in base_cls.__mro__):
                    try:
                        attr.overrides = mro_cls._attributes[name]
                        break
                    except KeyError:
                        pass
                else:
                    raise NotImplementedError
                doc.append('{0} (:class:`.{1}`): Overrides the default '
                           'set in :attr:`{2} <.{2}.{0}>`'
                           .format(name, attr.accepted_type.__name__,
                                   mro_cls.__name__))
            else:
                doc.append('{} (:class:`.{}`): {}'
                           .format(name, attr.accepted_type.__name__,
                                   attr.description))
            format = attr.accepted_type.doc_format()
            default = attr.accepted_type.doc_repr(attr.default_value)
            doc.append('\n            Accepts: {}\n'.format(format))
            doc.append('\n            Default: {}\n'.format(default))
        supported_attributes = list(name for name in attributes)
        for base_class in bases:
            try:
                supported_attributes.extend(base_class._supported_attributes)
            except AttributeError:
                continue
            for mro_cls in base_class.__mro__:
                for name, attr in getattr(mro_cls, '_attributes', {}).items():
                    if name in attributes:
                        continue
                    doc.append('{} (:class:`.{}`): (:attr:`{} <.{}.{}>`) {}'
                               .format(name, attr.accepted_type.__name__,
                                       mro_cls.__name__, mro_cls.__name__,
                                       name, attr.description))
                    format = attr.accepted_type.doc_format()
                    default = attr.accepted_type.doc_repr(attr.default_value)
                    doc.append('\n            Accepts: {}\n'.format(format))
                    doc.append('\n            Default: {}\n'.format(default))
        if doc:
            attr_doc = '\n        '.join(chain(['    Attributes:'], doc))
            cls_dict['__doc__'] = (cls_dict.get('__doc__', '') + '\n\n'
                                   + attr_doc)
        cls_dict['_supported_attributes'] = supported_attributes
        return super().__new__(mcls, classname, bases, cls_dict)

    @property
    def supported_attributes(cls):
        for mro_class in cls.__mro__:
            for name in getattr(mro_class, '_supported_attributes', ()):
                yield name


class AttributesDictionary(OrderedDict, metaclass=WithAttributes):
    default_base = None

    def __init__(self, base=None, **attributes):
        self.base = base or self.default_base
        for name, value in attributes.items():
            attributes[name] = self.validate_attribute(name, value, True)
        super().__init__(attributes)

    @classmethod
    def validate_attribute(cls, name, value, accept_variables):
        try:
            attribute_type = cls.attribute_definition(name).accepted_type
        except KeyError:
            raise TypeError('{} is not a supported attribute for {}'
                            .format(name, cls.__name__))
        return attribute_type.validate(value, accept_variables, name)

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
        raise KeyError(name)

    def get_value(self, attribute, rule_set):
        value = self[attribute]
        if isinstance(value, Var):
            accepted_type = self.attribute_definition(attribute).accepted_type
            value = value.get(accepted_type, rule_set)
            value = self.validate_attribute(attribute, value, False)
        return value


class RuleSet(OrderedDict):
    main_section = NotImplementedAttribute()

    def __init__(self, name, base=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.base = base
        self.variables = OrderedDict()

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
            if self.base:
                return self.base.get_variable(name, accepted_type)
            else:
                raise VariableNotDefined("Variable '{}' is not defined"
                                         .format(name))

    def _get_variable(self, name, accepted_type):
        return self.variables[name]

    def get_entry_class(self, name):
        raise NotImplementedError



class RuleSetFile(RuleSet):
    def __init__(self, filename, base=None, **kwargs):
        self.filename = filename
        config = ConfigParser(default_section=None, delimiters=('=',),
                              interpolation=None)
        with open(filename) as file:
            config.read_file(file)
        options = dict(config[self.main_section]
                       if config.has_section(self.main_section) else {})
        name = options.pop('name', filename)
        base = options.pop('base', base)
        options.update(kwargs)    # optionally override options
        super().__init__(name, base=base, **options)
        if config.has_section('VARIABLES'):
            for name, value in config.items('VARIABLES'):
                self.variables[name] = value
        for section_name, section_body in config.items():
            if section_name in (None, self.main_section, 'VARIABLES'):
                continue
            if ':' in section_name:
                name, classifier = (s.strip() for s in section_name.split(':'))
            else:
                name, classifier = section_name.strip(), None
            self.process_section(name, classifier, section_body.items())

    def _get_variable(self, name, accepted_type):
        variable = super()._get_variable(name, accepted_type)
        if isinstance(variable, str):
            variable = accepted_type.from_string(variable)
        return variable

    def process_section(self, section_name, classifier, items):
        raise NotImplementedError


class Bool(AttributeType):
    @classmethod
    def check_type(cls, value):
        return isinstance(value, bool)

    @classmethod
    def parse_string(cls, string):
        lower_string = string.lower()
        if lower_string not in ('true', 'false'):
            raise ValueError("'{}' is not a valid {}. Must be one of 'true' "
                             "or 'false'".format(string, cls.__name__))
        return lower_string == 'true'

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(str(value).lower())

    @classmethod
    def doc_format(cls):
        return '``true`` or ``false``'


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

    @classmethod
    def doc_format(cls):
        return 'a natural number (positive integer)'


# variables

class Var(object):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def __str__(self):
        return '$({})'.format(self.name)

    def get(self, accepted_type, rule_set):
        return rule_set.get_variable(self.name, accepted_type)


class VariableNotDefined(Exception):
    pass
