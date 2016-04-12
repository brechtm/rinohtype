# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Base classes and exceptions for styled document elements.

* :class:`Style`: Dictionary storing a set of style attributes
* :class:`Styled`: A styled entity, having a :class:`Style` associated with it
* :class:`StyleStore`: Dictionary storing a set of related `Style`s by name
* :const:`PARENT_STYLE`: Special style that forwards style lookups to the parent
                        :class:`Styled`
* :exc:`ParentStyleException`: Thrown when style attribute lookup needs to be
                               delegated to the parent :class:`Styled`
"""

import re

from ast import literal_eval
from configparser import ConfigParser
from collections import OrderedDict, namedtuple
from operator import attrgetter

from .element import DocumentElement
from .util import (cached, unique, all_subclasses, NamedDescriptor,
                   WithNamedDescriptors, NotImplementedAttribute)


__all__ = ['Style', 'Styled', 'Var', 'AttributeType', 'OptionSet', 'Attribute',
           'OverrideDefault', 'Bool', 'Integer', 'StyledMatcher', 'StyleSheet',
           'StyleSheetFile', 'ClassSelector', 'ContextSelector', 'PARENT_STYLE',
           'StyleException']


class StyleException(Exception):
    """Style lookup requires special handling."""


class ParentStyleException(StyleException):
    """Style attribute not found. Consult the parent :class:`Styled`."""


class BaseStyleException(StyleException):
    """The attribute is not specified in this :class:`Style`. Find the attribute
    in a base style."""

    def __init__(self, base_name, attribute):
        self.base_name = base_name
        self.attribute = attribute


class DefaultStyleException(StyleException):
    """The attribute is not specified in this :class:`Style` or any of its base
    styles. Return the default value for the attribute."""


class AttributeType(object):
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


class StyleMeta(WithNamedDescriptors):
    def __new__(cls, classname, bases, cls_dict):
        attributes = cls_dict['_attributes'] = {}
        for name, attr in cls_dict.items():
            if isinstance(attr, Attribute):
                attributes[name] = attr
            if isinstance(attr, OverrideDefault):
                for base_cls in bases:
                    try:
                        attr.overrides = base_cls.attribute_definition(name)
                        break
                    except KeyError:
                        pass
                else:
                    raise NotImplementedError
        supported_attributes = set(name for name in attributes)
        for base_class in bases:
            try:
                supported_attributes.update(base_class._supported_attributes)
            except AttributeError:
                pass
        cls_dict['_supported_attributes'] = supported_attributes
        return super().__new__(cls, classname, bases, cls_dict)


class Style(dict, metaclass=StyleMeta):
    """"Dictionary storing style attributes.

    The style attributes associated with this :class:`Style` are specified as
    class attributes of type :class:`Attribute`.

    Style attributes can also be accessed as object attributes."""

    default_base = None

    def __init__(self, base=None, **attributes):
        """Style attributes are as passed as keyword arguments. Supported
        attributes are the :class:`Attribute` class attributes of this style
        class and those defined in style classes this one inherits from.

        Optionally, a `base` (:class:`Style`) is passed, where attributes are
        looked up when they have not been specified in this style.
        Alternatively, if `base` is :class:`PARENT_STYLE`, the attribute lookup
        is forwarded to the parent of the element the lookup originates from.
        If `base` is a :class:`str`, it is used to look up the base style in
        the :class:`StyleSheet` this style is defined in."""
        self.base = base or self.default_base
        self.name = None
        for name, value in attributes.items():
            try:
                self._check_attribute_type(name, value, accept_variables=True)
            except KeyError:
                raise TypeError('{} is not a supported attribute for '
                                '{}'.format(name, type(self).__name__))
        super().__init__(attributes)

    def _check_attribute_type(self, name, value, accept_variables):
        attribute = self.attribute_definition(name)
        if not (attribute.accepted_type.check_type(value)
                or accept_variables and isinstance(value, VarBase)):
            type_name = type(value).__name__
            raise TypeError("{} ({}) is not of the correct type for the '{}' "
                            'style attribute'.format(value, type_name, name))

    def __repr__(self):
        """Return a textual representation of this style."""
        return '{0}({1}) > {2}'.format(self.__class__.__name__, self.name or '',
                                       self.base)

    def __copy__(self):
        copy = self.__class__(base=self.base, **self)
        if self.name is not None:
            copy.name = self.name + ' (copy)'
        return copy

    def __getattr__(self, attribute):
        if attribute in self._supported_attributes:
            return self[attribute]
        else:
            return super().__getattr__(attribute)

    def __getitem__(self, attribute):
        """Return the value of `attribute`.

        If the attribute is not specified in this :class:`Style`, find it in
        this style's base styles (hierarchically), or ultimately raise a
        :class:`DefaultValueException`."""
        try:
            return super().__getitem__(attribute)
        except KeyError:
            if self.base is None:
                raise DefaultStyleException
            elif isinstance(self.base, str):
                raise BaseStyleException(self.base, attribute)
            else:
                return self.base[attribute]

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

    def get_value(self, attribute, document):
        value = self[attribute]
        if isinstance(value, VarBase):
            accepted_type = self.attribute_definition(attribute).accepted_type
            value = value.get(accepted_type, document)
            self._check_attribute_type(attribute, value, accept_variables=False)
        return value


class ParentStyle(Style):
    """Special style that delegates attribute lookups by raising a
    :class:`ParentStyleException` on each attempt to access an attribute."""

    def __repr__(self):
        return self.__class__.__name__

    def __getitem__(self, attribute):
        raise ParentStyleException

    def __bool__(self):
        return True


PARENT_STYLE = ParentStyle()
"""Special style that forwards style lookups to the parent of the
:class:`Styled` from which the lookup originates."""


class Selector(object):
    cls = NotImplementedAttribute

    def __truediv__(self, other):
        try:
            selectors = self.selectors + other.selectors
        except AttributeError:
            if isinstance(other, str):
                selectors = self.selectors + (SelectorByName(other), )
            else:
                assert other == Ellipsis
                selectors = self.selectors + (EllipsisSelector(), )
        return ContextSelector(*selectors)

    def __rtruediv__(self, other):
        assert isinstance(other, str)
        return SelectorByName(other) / self

    def get_styled_class(self, matcher):
        raise NotImplementedError

    def get_style_name(self, matcher):
        raise NotImplementedError

    @property
    def referenced_selectors(self):
        raise NotImplementedError

    def match(self, styled, container):
        raise NotImplementedError


class EllipsisSelector(Selector):
    @property
    def referenced_selectors(self):
        return
        yield


class SingleSelector(Selector):
    @property
    def selectors(self):
        return (self, )


class SelectorByName(SingleSelector):
    def __init__(self, name):
        self.name = name

    @property
    def referenced_selectors(self):
        yield self.name

    def get_styled_class(self, matcher):
        selector = matcher.by_name[self.name]
        return selector.get_styled_class(matcher)

    def get_style_name(self, matcher):
        selector = matcher.by_name[self.name]
        return selector.get_style_name(matcher)

    def match(self, styled, container):
        selector = container.document.stylesheet.get_selector(self.name)
        return selector.match(styled, container)


class ClassSelectorBase(SingleSelector):
    def get_styled_class(self, matcher):
        return self.cls

    @property
    def referenced_selectors(self):
        return
        yield

    def get_style_name(self, matcher):
        return self.style_name

    def match(self, styled, container):
        if not isinstance(styled, self.cls):
            return None
        class_match = 2 if type(styled) == self.cls else 1

        style_match = 0
        if self.style_name is not None:
            if styled.style != self.style_name:
                return None
            style_match = 1

        attributes_match = 0
        for attr, value in self.attributes.items():
            if not hasattr(styled, attr) or getattr(styled, attr) != value:
                return None
            attributes_match += 1

        return Specificity(0, style_match, attributes_match, class_match)


class ClassSelector(ClassSelectorBase):
    def __init__(self, cls, style_name=None, **attributes):
        super().__init__()
        self.cls = cls
        self.style_name = style_name
        self.attributes = attributes


class ContextSelector(Selector):
    def __init__(self, *selectors):
        super().__init__()
        self.selectors = selectors

    @property
    def referenced_selectors(self):
        for selector in self.selectors:
            for name in selector.referenced_selectors:
                yield name

    def get_styled_class(self, matcher):
        return self.selectors[-1].get_styled_class(matcher)

    def get_style_name(self, matcher):
        return self.selectors[-1].get_style_name(matcher)

    def match(self, styled, container):
        def styled_and_parents(element):
            while element is not None:
                yield element
                element = element.parent
            raise NoMoreParentElement

        total_score = ZERO_SPECIFICITY
        selectors = reversed(self.selectors)
        elements = styled_and_parents(styled)
        for selector in selectors:
            try:
                element = next(elements)                # NoMoreParentElement
                if isinstance(selector, EllipsisSelector):
                    selector = next(selectors)          # StopIteration
                    while not selector.match(element, container):
                        element = next(elements)        # NoMoreParentElement
            except NoMoreParentElement:
                return None
            except StopIteration:
                break
            score = selector.match(element, container)
            if not score:
                return None
            total_score += score
        return total_score


class NoMoreParentElement(StopIteration):
    """The top-level element in the document element tree has been reached"""


class DocumentLocationType(type):
    def __gt__(cls, selector):
        return DocumentLocationSelector(cls, selector)

    def match(self, styled, container):
        raise NotImplementedError


class DocumentLocationSelector(object):
    def __init__(self, location_class, selector):
        self.location_class = location_class
        self.selector = selector

    @property
    def referenced_selectors(self):
        return
        yield

    def get_styled_class(self, matcher):
        return self.selector.get_styled_class(matcher)

    def get_style_name(self, matcher):
        return self.selector.get_style_name(matcher)

    def match(self, styled, container):
        location_match = self.location_class.match(styled, container)
        if location_match:
            match = self.selector.match(styled, container)
            if match:
                return location_match + match
        return None


class StyledMeta(type, ClassSelectorBase):
    attributes = {}
    style_name = None

    @property
    def cls(cls):
        return cls

    def like(cls, style_name=None, **attributes):
        return ClassSelector(cls, style_name, **attributes)


class Styled(DocumentElement, metaclass=StyledMeta):
    """An element that has a :class:`Style` associated with it."""

    style_class = None
    """The :class:`Style` subclass that corresponds to this :class:`Styled`
    subclass."""

    def __init__(self, id=None, style=None, parent=None):
        """Associates `style` with this element. If `style` is `None`, an empty
        :class:`Style` is create, effectively using the defaults defined for the
        associated :class:`Style` class).
        A `parent` can be passed on object initialization, or later by
        assignment to the `parent` attribute."""
        super().__init__(id=id, parent=parent)
        if (isinstance(style, Style)
                and not isinstance(style, (self.style_class, ParentStyle))):
            raise TypeError('the style passed to {} should be of type {} '
                            '(a {} was passed instead)'
                            .format(self.__class__.__name__,
                                    self.style_class.__name__,
                                    style.__class__.__name__))
        self.style = style

    @property
    def path(self):
        parent = self.parent.path + ' > ' if self.parent else ''
        style = '[{}]'.format(self.style) if self.style else ''
        return parent + self.__class__.__name__ + style

    @property
    def nesting_level(self):
        try:
            return self.parent.nesting_level + 1
        except AttributeError:
            return 0

    @cached
    def get_style(self, attribute, flowable_target):
        try:
            return self.get_style_recursive(attribute, flowable_target)
        except DefaultStyleException:
            # self.warn('Falling back to default style for ({})'
            #           .format(self.path))
            return self.style_class._get_default(attribute)

    def get_base_style_recursive(self, exception, flowable_target):
        document = flowable_target.document
        try:
            base_style = document.stylesheet[exception.base_name]
            return base_style.get_value(exception.attribute, document)
        except ParentStyleException:
            return self.parent.get_style_recursive(exception.attribute,
                                                   flowable_target)
        except BaseStyleException as e:
            return self.get_base_style_recursive(e, flowable_target)

    def get_style_recursive(self, attribute, flowable_target):
        try:
            try:
                style = self._style(flowable_target)
                return style.get_value(attribute, flowable_target.document)
            except DefaultStyleException:
                if self.style_class.default_base == PARENT_STYLE:
                    raise ParentStyleException
                raise
        except ParentStyleException:
            return self.parent.get_style_recursive(attribute, flowable_target)
        except BaseStyleException as exception:
            return self.get_base_style_recursive(exception, flowable_target)

    @cached
    def _style(self, container):
        if isinstance(self.style, Style):
            return self.style
        else:
            return container.document.stylesheet.find_style(self, container)
        raise DefaultStyleException


class InvalidStyledMatcher(Exception):
    """The :class:`StyledMatcher` includes selectors which reference selectors
    which are not defined."""

    def __init__(self, missing_selectors):
        self.missing_selectors = missing_selectors


class StyledMatcher(dict):
    def __init__(self, iterable=None, **kwargs):
        super().__init__()
        self.by_name = {}
        self._pending = {}
        self.update(iterable, **kwargs)

    def __call__(self, name, selector):
        self[name] = selector
        return SelectorByName(name)

    def __setitem__(self, name, selector):
        assert name not in self
        is_pending = False
        for referenced_name in unique(selector.referenced_selectors):
            if referenced_name not in self.by_name:
                pending_selectors = self._pending.setdefault(referenced_name, {})
                pending_selectors[name] = selector
                is_pending = True
        if not is_pending:
            cls_selectors = self.setdefault(selector.get_styled_class(self), {})
            style_name = selector.get_style_name(self)
            style_selectors = cls_selectors.setdefault(style_name, {})
            self.by_name[name] = style_selectors[name] = selector
            self._process_pending(name)

    def _process_pending(self, newly_defined_name):
        if newly_defined_name in self._pending:
            self.update(self._pending.pop(newly_defined_name))

    def check_validity(self):
        if self._pending:
            raise InvalidStyledMatcher(list(self._pending.keys()))

    def update(self, iterable=None, **kwargs):
        for name, selector in dict(iterable or (), **kwargs).items():
            self[name] = selector

    def match(self, styled, container):
        for cls in type(styled).__mro__:
            if cls not in self:
                continue
            style_str = styled.style if isinstance(styled.style, str) else None
            for style in set((style_str, None)):
                for name, selector in self[cls].get(style, {}).items():
                    specificity = selector.match(styled, container)
                    if specificity:
                        yield Match(name, specificity)


class StyleSheet(OrderedDict, AttributeType):
    """Dictionary storing a set of related :class:`Style`s by name.

    :class:`Style`s stored in a :class:`StyleStore` can refer to their base
    style by name. See :class:`Style`."""

    def __init__(self, name, matcher=None, base=None):
        super().__init__()
        self.name = name
        self.matcher = matcher or base.matcher
        self.matcher.check_validity()
        self.base = base
        self.variables = {}

    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            if self.base is not None:
                return self.base[name]
            else:
                raise

    def __setitem__(self, name, style):
        assert name not in self
        style.name = name
        super().__setitem__(name, style)

    def __call__(self, name, **kwargs):
        self[name] = self.get_style_class(name)(**kwargs)

    def __str__(self):
        return '{}({})'.format(type(self).__name__, self.name)

    def get_styled(self, name):
        style_sheet = self
        while style_sheet is not None:
            try:
                selector = style_sheet.matcher.by_name[name]
                return selector.get_styled_class(style_sheet.matcher)
            except KeyError:
                style_sheet = style_sheet.base
        raise KeyError("No selector found for style '{}'".format(name))

    def get_style_class(self, name):
        return self.get_styled(name).style_class

    def get_variable(self, name, accepted_type):
        try:
            return self._get_variable(name, accepted_type)
        except KeyError:
            return self.base.get_variable(name, accepted_type)

    def _get_variable(self, name, accepted_type):
        return self.variables[name]

    def get_selector(self, name):
        try:
            return self.matcher.by_name[name]
        except KeyError:
            if self.base is not None:
                return self.base.get_selector(name)
            else:
                raise

    def find_matches(self, styled, container):
        for match in self.matcher.match(styled, container):
            yield match
        if self.base is not None:
            for match in self.base.find_matches(styled, container):
                yield match

    def find_style(self, styled, container):
        matches = sorted(self.find_matches(styled, container),
                         key=attrgetter('specificity'), reverse=True)
        for match in matches:
            try:
                # print("({}) matches '{}'".format(styled.path,
                #                                  match.style_name))
                return self[match.style_name]
            except KeyError:
                styled.warn("No style '{}' found in stylesheet"
                            .format(match.style_name), container)
        raise DefaultStyleException


class StyleSheetFile(StyleSheet):
    RE_VARIABLE = re.compile(r'^\$\(([a-z_ -]+)\)$', re.IGNORECASE)
    RE_SELECTOR = re.compile(r'^(?P<name>[a-z]+)\((?P<args>.*)\)$', re.I)

    def __init__(self, filename, matcher, base=None):
        config = ConfigParser(default_section=None, delimiters=('=',),
                              comment_prefixes=('#', ), interpolation=None)
        with open(filename) as file:
            config.read_file(file)
        super().__init__(filename, matcher, base)
        for section_name, section_body in config.items():
            if section_name is None:    # default section
                continue
            if section_name == 'VARIABLES':
                for name, value in section_body.items():
                    self.variables[name] = value
                continue
            try:
                style_name, selector  = section_name.split(':')
                m = self.RE_SELECTOR.match(selector)
                if m:
                    styled_name = m.group('name')
                    selector_args = m.group('args')
                else:
                    styled_name = selector
                    selector_args = None
                for styled_class in all_subclasses(Styled):
                    if styled_class.__name__ == styled_name:
                        style_cls = styled_class.style_class
                        break
                else:
                    raise TypeError("Invalid type '{}' given for style '{}'"
                                    .format(styled_name, style_name))
                if selector_args:
                    args, kwargs = parse_selector_args(selector_args)
                    selector = styled_class.like(*args, **kwargs)
                    self.matcher[style_name] = selector
                try:
                    matcher_styled = self.get_styled(style_name)
                    if styled_class is not matcher_styled:
                        raise TypeError("The type '{}' specified for style "
                                        "'{}' does not match the type '{}' "
                                        "returned by the matcher. Note that "
                                        "you do not have to specify the type "
                                        "in this case!"
                                        .format(styled_class.__name__,
                                                style_name,
                                                matcher_styled.__name__))
                except KeyError:
                    pass
            except ValueError:
                style_name = section_name
                style_cls = self.get_style_class(style_name)
            attribute_values = {}
            for name, value in section_body.items():
                value = value.replace('\n', ' ')
                if name == 'base':
                    attribute_values[name] = value
                else:
                    try:
                        attribute = style_cls.attribute_definition(name)
                    except KeyError:
                        raise TypeError("'{}' is not a supported attribute for "
                                        "'{}' ({})".format(name, style_name,
                                                           style_cls.__name__))
                    stripped = value.strip()
                    m = self.RE_VARIABLE.match(stripped)
                    if m:
                        variable_name, = m.groups()
                        value = Var(variable_name)
                    else:
                        accepted_type = attribute.accepted_type
                        value = accepted_type.from_string(stripped)
                    attribute_values[name] = value
            self[style_name] = style_cls(**attribute_values)

    def _get_variable(self, name, accepted_type):
        return accepted_type.from_string(self.variables[name])


class StyleParseError(Exception):
    pass


def parse_selector_args(selector_args):
    args, kwargs = [], {}
    chars = CharIterator(selector_args)
    try:
        while True:
            eat_whitespace(chars)
            argument = parse_value(chars)
            if argument is not None:
                assert not kwargs
                args.append(argument)
            else:
                keyword = parse_keyword(chars)
                eat_whitespace(chars)
                kwargs[keyword] = parse_value(chars)
            eat_whitespace(chars)
            assert next(chars) == ','
    except StopIteration:
        pass
    return args, kwargs


def eat_whitespace(chars):
    for char in chars:
        if char not in ' \t':
            chars.push_back(char)
            break


class CharIterator(object):
    def __init__(self, string):
        self._iter = iter(string)
        self._pushed_back = []

    def __iter__(self):
        return self

    def __next__(self):
        if self._pushed_back:
            return self._pushed_back.pop(0)
        return next(self._iter)

    def push_back(self, char):
        self._pushed_back.insert(0, char)


def parse_keyword(chars):
    keyword_chars = []
    for char in chars:
        if not (char.isalnum() or char == '_'):
            break
        keyword_chars.append(char)
    try:
        while char != '=':
            assert char in ' \t'
            char = next(chars)
    except (StopIteration, AssertionError):
        raise StyleParseError('Expecting an equals sign to follow a keyword')
    return ''.join(keyword_chars)


def parse_value(chars):
    first_char = next(chars)
    if first_char in ("'", '"'):
        argument = parse_string(first_char, chars)
    elif first_char.isnumeric() or first_char in '+-':
        argument = parse_number(first_char, chars)
    else:
        chars.push_back(first_char)
        argument = None
    return argument


def parse_string(open_quote, chars):
    string_chars = [open_quote]
    escape_next = False
    for char in chars:
        string_chars.append(char)
        if char == '\\':
            escape_next = True
            continue
        elif not escape_next and char == open_quote:
            break
        escape_next = False
    else:
        raise StyleParseError('Did not encounter a closing '
                              'quote while parsing string')
    return literal_eval(''.join(string_chars))


def parse_number(first_char, chars):
    number_chars = [first_char]
    for char in chars:
        if char not in '0123456789.e+-':
            chars.push_back(char)
            break
        number_chars.append(char)
    return literal_eval(''.join(number_chars))


class VarBase(object):
    def __getattr__(self, name):
        return VarAttribute(self, name)

    def get(self, style, attribute, document):
        raise NotImplementedError


class Var(VarBase):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def get(self, accepted_type, document):
        return document.get_style_var(self.name, accepted_type)


class VarAttribute(VarBase):
    def __init__(self, parent, attribute_name):
        super().__init__()
        self.parent = parent
        self.attribute_name = attribute_name

    def get(self, accepted_type, document):
        return getattr(self.parent.get(accepted_type, document),
                       self.attribute_name)


class Specificity(namedtuple('Specificity',
                             ['location', 'style', 'attributes', 'klass'])):
    def __add__(self, other):
        return self.__class__(*(a + b for a, b in zip(self, other)))

    def __bool__(self):
        return any(self)


class Match(object):
    def __init__(self, style_name, specificity):
        self.style_name = style_name
        self.specificity = specificity

    def __gt__(self, other):
        return self.specificity > other.specificity

    def __bool__(self):
        return bool(self.specificity)


ZERO_SPECIFICITY = Specificity(0, 0, 0, 0)

NO_MATCH = Match(None, ZERO_SPECIFICITY)


class StyleLogEntry(object):
    def __init__(self, styled, page_number, matches, custom_message=None):
        self.styled = styled
        self.page_number = page_number
        self.matches = matches
        self.custom_message = custom_message


class StyleLog(object):
    def __init__(self, stylesheet):
        self.stylesheet = stylesheet
        self.entries = []

    def log_styled(self, styled, container, custom_message=None):
        page_number = container.page.number
        matches = self.stylesheet.find_matches(styled, container)
        log_entry = StyleLogEntry(styled, page_number, matches, custom_message)
        self.entries.append(log_entry)

    def log_out_of_line(self):
        raise NotImplementedError

    def write_log(self, filename_root):
        with open(filename_root + '.stylelog', 'w') as log:
            current_page = None
            for entry in self.entries:
                if entry.page_number != current_page:
                    current_page = entry.page_number
                    log.write('{line} page {} {line}\n'.format(current_page,
                                                               line='-' * 34))
                styled = entry.styled
                level = styled.nesting_level
                name = type(styled).__name__
                attrs = OrderedDict()
                if styled.id:
                    attrs['id'] = "'{}'".format(styled.id)
                if styled.style:
                    attrs['style'] = "'{}'".format(styled.style)
                attr_repr = ', '.join(key + '=' + value
                                      for key, value in attrs.items())
                indent = '  ' * level
                log.write('{}{}({}) {}' .format(indent, name, attr_repr,
                                                styled.source.location))
                if entry.custom_message:
                    log.write('\n    {} ! {}'.format(indent,
                                                     entry.custom_message))
                else:
                    matches = sorted(entry.matches, reverse=True,
                                     key=attrgetter('specificity'))
                    first = True
                    style = None
                    for match in matches:
                        try:
                            _ = self.stylesheet[match.style_name]
                            if first:
                                style = _
                                label = '>'
                                first = False
                            else:
                                label = ' '
                        except KeyError:
                            label = 'x'
                        specificity = ','.join(str(score)
                                               for score in match.specificity)
                        log.write('\n    {} {} ({}) {}'
                                  .format(indent, label, specificity,
                                          match.style_name))
                    if not matches:
                        log.write(' - default style')
                    elif style is None:
                        log.write('\n    {} > fallback to default style'
                                  .format(indent))
                log.write('\n')
