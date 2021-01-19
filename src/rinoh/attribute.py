# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from collections import OrderedDict
from configparser import ConfigParser
from io import StringIO
from itertools import chain
from pathlib import Path
from token import NUMBER, ENDMARKER, MINUS, PLUS, NAME, NEWLINE
from tokenize import generate_tokens
from warnings import warn

from .util import (NamedDescriptor, WithNamedDescriptors,
                   NotImplementedAttribute, class_property, PeekIterator,
                   cached)


__all__ = ['AttributeType', 'AcceptNoneAttributeType', 'OptionSet',
           'OptionSetMeta', 'Attribute', 'OverrideDefault',
           'AttributesDictionary', 'Configurable', 'RuleSet', 'RuleSetFile',
           'Bool', 'Integer', 'ParseError', 'Var']


class AttributeType(object):
    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    @classmethod
    def check_type(cls, value):
        return isinstance(value, cls)

    @classmethod
    def from_string(cls, string, source=None):
        return cls.parse_string(string, source)

    @classmethod
    def parse_string(cls, string, source):
        tokens = TokenIterator(string)
        value = cls.from_tokens(tokens, source)
        if next(tokens).type != ENDMARKER:
            raise ParseError('Syntax error')
        return value

    @classmethod
    def from_tokens(cls, tokens, source):
        raise NotImplementedError(cls)

    @classmethod
    def validate(cls, value):
        if isinstance(value, str):
            value = cls.from_string(value)
        if not cls.check_type(value):
            raise TypeError("{} is not of type {}".format(value, cls.__name__))
        return value

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(value) if value else '(no value)'

    @classmethod
    def doc_format(cls):
        warn('Missing implementation for {}.doc_format'.format(cls.__name__))
        return ''


class AcceptNoneAttributeType(AttributeType):
    """Accepts 'none' (besides other values)"""

    @classmethod
    def check_type(cls, value):
        return (isinstance(value, type(None))
                or super(__class__, cls).check_type(value))

    @classmethod
    def from_string(cls, string, source=None):
        if string.strip().lower() == 'none':
            return None
        return super(__class__, cls).from_string(string, source)

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
    def _value_from_tokens(cls, tokens):
        if tokens.next.type != NAME:
            raise ParseError('Expecting a name')
        token = next(tokens)
        _, start_col = token.start
        while tokens.next and tokens.next.exact_type in (NAME, MINUS):
            token = next(tokens)
        _, end_col = token.end
        return token.line[start_col:end_col].strip()

    @classmethod
    def from_tokens(cls, tokens, source):
        option_string = cls._value_from_tokens(tokens)
        try:
            index = cls.value_strings.index(option_string.lower())
        except ValueError:
            raise ValueError("'{}' is not a valid {}. Must be one of: '{}'"
                             .format(option_string, cls.__name__,
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
        self.source = None

    def __get__(self, style, type=None):
        try:
            return style.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, style, value):
        if not self.accepted_type.check_type(value):
            raise TypeError('The {} attribute only accepts {} instances'
                            .format(self.name, self.accepted_type.__name__))
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
                doc.append('{0}: Overrides the default '
                           'set in :attr:`{1} <.{1}.{0}>`'
                           .format(name, mro_cls.__name__))
            else:
                doc.append('{}: {}'.format(name, attr.description))
            format = attr.accepted_type.doc_format()
            default = attr.accepted_type.doc_repr(attr.default_value)
            doc.append('\n            *Accepts* :class:`.{}`: {}\n'
                       .format(attr.accepted_type.__name__, format))
            doc.append('\n            *Default*: {}\n'.format(default))
        supported_attributes = list(name for name in attributes)
        documented = set(supported_attributes)
        for base_class in bases:
            try:
                supported_attributes.extend(base_class._supported_attributes)
            except AttributeError:
                continue
            for mro_cls in base_class.__mro__:
                for name, attr in getattr(mro_cls, '_attributes', {}).items():
                    if name in documented:
                        continue
                    doc.append('{0}: {1} (inherited from :attr:`{2} <.{2}.{0}>`)'
                               .format(name, attr.description,
                                       mro_cls.__name__))
                    format = attr.accepted_type.doc_format()
                    default = attr.accepted_type.doc_repr(attr.default_value)
                    doc.append('\n            *Accepts* :class:`.{}`: {}\n'
                               .format(attr.accepted_type.__name__, format))
                    doc.append('\n            *Default*: {}\n'.format(default))
                    documented.add(name)
        if doc:
            attr_doc = '\n        '.join(chain(['    Attributes:'], doc))
            cls_dict['__doc__'] = (cls_dict.get('__doc__', '') + '\n\n'
                                   + attr_doc)
        cls_dict['_supported_attributes'] = supported_attributes
        return super().__new__(mcls, classname, bases, cls_dict)

    @property
    def _all_attributes(cls):
        for mro_class in reversed(cls.__mro__):
            for name in getattr(mro_class, '_attributes', ()):
                yield name

    @property
    def supported_attributes(cls):
        for mro_class in cls.__mro__:
            for name in getattr(mro_class, '_supported_attributes', ()):
                yield name


class AttributesDictionary(OrderedDict, metaclass=WithAttributes):
    def __init__(self, base=None, **attributes):
        self.name = None
        self.source = None
        self.base = base
        super().__init__(attributes)

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

    @classmethod
    def attribute_type(cls, name):
        try:
            return cls.attribute_definition(name).accepted_type
        except KeyError:
            raise TypeError('{} is not a supported attribute for {}'
                            .format(name, cls.__name__))

    @classmethod
    def get_ruleset(self):
        raise NotImplementedError


class DefaultValueException(Exception):
    pass


class Configurable(object):
    configuration_class = NotImplementedAttribute()

    def configuration_name(self, document):
        raise NotImplementedError

    def get_config_value(self, attribute, document):
        ruleset = self.configuration_class.get_ruleset(document)
        return ruleset.get_value_for(self, attribute, document)


class BaseConfigurationException(Exception):
    def __init__(self, base_name):
        self.name = base_name


class Source(object):
    """Describes where a :class:`DocumentElement` was defined"""

    @property
    def location(self):
        """Textual representation of this source"""
        return repr(self)

    @property
    def root(self):
        """Directory path for resolving paths relative to this source"""
        return None


class RuleSet(OrderedDict, Source):
    main_section = NotImplementedAttribute()

    def __init__(self, name, base=None, source=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.base = base
        self.source = source
        self.variables = OrderedDict()

    def contains(self, name):
        return name in self or (self.base and self.base.contains(name))

    def get_configuration(self, name):
        try:
            return self[name]
        except KeyError:
            if self.base:
                return self.base.get_configuration(name)
            raise

    def __setitem__(self, name, item):
        assert name not in self
        if isinstance(item, AttributesDictionary):  # FIXME
            self._validate_attributes(name, item)
        super().__setitem__(name, item)

    def __call__(self, name, **kwargs):
        self[name] = self.get_entry_class(name)(**kwargs)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.name)

    def __str__(self):
        return repr(self)

    def __bool__(self):
        return True

    RE_VARIABLE = re.compile(r'^\$\(([a-z_ -]+)\)$', re.IGNORECASE)

    def _validate_attributes(self, name, attr_dict):
        attr_dict.name = name
        attr_dict.source = self
        for key, val in attr_dict.items():
            attr_dict[key] = self._validate_attribute(attr_dict, key, val)

    def _validate_attribute(self, attr_dict, name, value):
        attribute_type = attr_dict.attribute_type(name)
        if isinstance(value, str):
            stripped = value.replace('\n', ' ').strip()
            m = self.RE_VARIABLE.match(stripped)
            if m:
                return Var(m.group(1))
            value = self._attribute_from_string(attribute_type, stripped)
        elif hasattr(value, 'source'):
            value.source = self
        if not isinstance(value, Var) and not attribute_type.check_type(value):
            raise TypeError("{} ({}) is not of the correct type for the '{}' "
                            "attribute".format(value, type(value).__name__,
                                               name))
        return value

    @cached
    def _attribute_from_string(self, attribute_type, string):
        return attribute_type.from_string(string, self)

    def get_variable(self, configuration_class, attribute, variable):
        try:
            value = self.variables[variable.name]
        except KeyError:
            if not self.base:
                raise VariableNotDefined("Variable '{}' is not defined"
                                         .format(variable.name))
            return self.base.get_variable(configuration_class, attribute,
                                          variable)
        return self._validate_attribute(configuration_class, attribute, value)

    def get_entry_class(self, name):
        raise NotImplementedError

    def _get_value_recursive(self, name, attribute):
        if name in self:
            entry = self[name]
            if attribute in entry:
                return entry[attribute]
            elif isinstance(entry.base, str):
                raise BaseConfigurationException(entry.base)
            elif entry.base is not None:
                return entry.base[attribute]
        if self.base:
            return self.base._get_value_recursive(name, attribute)
        raise DefaultValueException

    @cached
    def get_value(self, name, attribute):
        try:
            return self._get_value_recursive(name, attribute)
        except BaseConfigurationException as exc:
            return self.get_value(exc.name, attribute)

    def _get_value_lookup(self, configurable, attribute, document):
        name = configurable.configuration_name(document)
        return self.get_value(name, attribute)

    def get_value_for(self, configurable, attribute, document):
        try:
            value = self._get_value_lookup(configurable, attribute, document)
        except DefaultValueException:
            value = configurable.configuration_class._get_default(attribute)
        if isinstance(value, Var):
            configuration_class = configurable.configuration_class
            value = self.get_variable(configuration_class, attribute, value)
        return value


class RuleSetFile(RuleSet):
    def __init__(self, filename, base=None, source=None, **kwargs):
        self.filename = self._absolute_path(filename, source)
        config = ConfigParser(default_section=None, delimiters=('=',),
                              interpolation=None)
        with self.filename.open() as file:
            config.read_file(file)
        options = dict(config[self.main_section]
                       if config.has_section(self.main_section) else {})
        name = options.pop('name', filename)
        base = options.pop('base', base)
        options.update(kwargs)    # optionally override options
        super().__init__(name, base=base, source=source, **options)
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

    @classmethod
    def _absolute_path(cls, filename, source):
        file_path = Path(filename)
        if not file_path.is_absolute():
            if source is None or source.root is None:
                raise ValueError('{} path should be absolute: {}'
                                 .format(cls.__name__, file_path))
            file_path = source.root / file_path
        return file_path

    @property
    def location(self):
        return str(self.filename.resolve())

    @property
    def root(self):
        return self.filename.parent.resolve()

    def process_section(self, section_name, classifier, items):
        raise NotImplementedError


class Bool(AttributeType):
    """Expresses a binary choice"""

    @classmethod
    def check_type(cls, value):
        return isinstance(value, bool)

    @classmethod
    def from_tokens(cls, tokens, source):
        string = next(tokens).string
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
    """Accepts natural numbers"""

    @classmethod
    def check_type(cls, value):
        return isinstance(value, int)

    @classmethod
    def from_tokens(cls, tokens, source):
        token = next(tokens)
        sign = 1
        if token.exact_type in (MINUS, PLUS):
            sign = 1 if token.exact_type == PLUS else -1
            token = next(tokens)
        if token.type != NUMBER:
            raise ParseError('Expecting a number')
        try:
            value = int(token.string)
        except ValueError:
            raise ParseError('Expecting an integer')
        return sign * value

    @classmethod
    def doc_format(cls):
        return 'a natural number (positive integer)'


class TokenIterator(PeekIterator):
    """Tokenizes `string` and iterates over the tokens"""

    def __init__(self, string):
        self.string = string
        tokens = generate_tokens(StringIO(string).readline)
        super().__init__(tokens)

    def _advance(self):
        result = super()._advance()
        if self.next and self.next.type == NEWLINE and self.next.string == '':
            super()._advance()
        return result


class ParseError(Exception):
    pass


# variables

class Var(object):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def __str__(self):
        return '$({})'.format(self.name)

    def __eq__(self, other):
        return self.name == other.name


class VariableNotDefined(Exception):
    pass
