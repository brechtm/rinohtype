# This file is part of rinohtype, the Python document preparation system.
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
from itertools import chain
from operator import attrgetter

from .attribute import AttributesDictionary, RuleSet, Var
from .element import DocumentElement
from .resource import Resource
from .util import cached, unique, all_subclasses, NotImplementedAttribute
from .warnings import warn


__all__ = ['Style', 'Styled', 'StyledMatcher', 'StyleSheet', 'StyleSheetFile',
           'ClassSelector', 'ContextSelector', 'PARENT_STYLE', 'StyleException']


class StyleException(Exception):
    """Style lookup requires special handling."""


class ParentStyleException(StyleException):
    """Style attribute not found. Consult the parent :class:`Styled`."""


class BaseStyleException(StyleException):
    """The `attribute` is not specified in this :class:`Style`. Try to find the
    attribute in a base style instead."""

    def __init__(self, base_name, attribute):
        self.base_name = base_name
        self.attribute = attribute


class DefaultStyleException(StyleException):
    """The attribute is not specified in this :class:`Style` or any of its base
    styles. Return the default value for the attribute."""


class NoStyleException(StyleException):
    """No style matching the given :class:`Styled` was found in the
    :class:`StyleSheet`."""


class Style(AttributesDictionary):
    """Dictionary storing style attributes.

    The style attributes associated with this :class:`Style` are specified as
    class attributes of type :class:`Attribute`.

    Style attributes can also be accessed as object attributes.

    """

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
        super().__init__(base, **attributes)

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

    def __pos__(self):
        return self.pri(1)

    def __neg__(self):
        return self.pri(-1)

    def pri(self, priority):
        return SelectorWithPriority(self, priority)

    def get_styled_class(self, matcher):
        raise NotImplementedError

    def get_style_name(self, matcher):
        raise NotImplementedError

    @property
    def referenced_selectors(self):
        raise NotImplementedError

    def match(self, styled, container):
        raise NotImplementedError


class SelectorWithPriority(Selector):
    def __init__(self, selector, priority):
        self.selector = selector
        self.priority = priority

    def pri(self, priority):
        return SelectorWithPriority(self.selector, self.priority + priority)

    def get_styled_class(self, matcher):
        return self.selector.get_styled_class(matcher)

    def get_style_name(self, matcher):
        return self.selector.get_style_name(matcher)

    @property
    def selectors(self):
        return (self, )

    @property
    def referenced_selectors(self):
        return self.selector.referenced_selectors

    def flatten(self, container):
        flattened_selector = self.selector.flatten(container)
        return flattened_selector.pri(self.priority)

    def match(self, styled, container):
        score = self.selector.match(styled, container)
        if score:
            score = Specificity(self.priority, 0, 0, 0, 0) + score
        return score


class EllipsisSelector(Selector):
    @property
    def selectors(self):
        return (self, )

    @property
    def referenced_selectors(self):
        return
        yield

    def flatten(self, container):
        return self


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

    def flatten(self, container):
        return container.document.stylesheet.get_selector(self.name)

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

    def flatten(self, container):
        return self

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

        return Specificity(0, 0, style_match, attributes_match, class_match)


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

    def flatten(self, container):
        return type(self)(*(child_selector for selector in self.selectors
                            for child_selector
                            in selector.flatten(container).selectors))

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
    """A document element who's style can be configured.

    Args:
        style (str, Style): the style to associate with this element. If
            `style` is a string, the corresponding style is lookup up in the
            document's style sheet by means of selectors.

    """

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

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def short_repr(self, flowable_target):
        args = ', '.join(chain(self._short_repr_args(flowable_target),
                               self._short_repr_kwargs(flowable_target)))
        return '{}({})'.format(type(self).__name__, args)

    def _short_repr_args(self, flowable_target):
        return ()

    def _short_repr_kwargs(self, flowable_target):
        if self.id:
            yield "id='{}'".format(self.id)
        if isinstance(self.style, str):
            yield "style='{}'".format(self.style)
        elif isinstance(self.style, Style):
            yield 'style={}'.format(type(self.style).__name__)

    SHORT_REPR_STRING_LENGTH = 32

    def _short_repr_string(self, flowable_target):
        text = self.to_string(flowable_target)
        if len(text) > self.SHORT_REPR_STRING_LENGTH:
            text = text[:self.SHORT_REPR_STRING_LENGTH] + '...'
        return "'{}'".format(text).replace('\n', '\\n')

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
            return self.style_class._get_default(attribute)

    def get_base_style_recursive(self, exception, flowable_target):
        stylesheet = flowable_target.document.stylesheet
        try:
            base_style = stylesheet[exception.base_name]
            return base_style.get_value(exception.attribute, stylesheet)
        except ParentStyleException:
            return self.parent.get_style_recursive(exception.attribute,
                                                   flowable_target)
        except BaseStyleException as e:
            return self.get_base_style_recursive(e, flowable_target)

    def get_style_recursive(self, attribute, flowable_target):
        stylesheet = flowable_target.document.stylesheet
        try:
            try:
                style = self._style(flowable_target)
                return style.get_value(attribute, stylesheet)
            except NoStyleException:
                if self.style_class.default_base == PARENT_STYLE:
                    raise ParentStyleException
                else:
                    raise DefaultStyleException
        except ParentStyleException:
            parent = self.parent
            try:
                return parent.get_style(attribute, flowable_target)
            except KeyError:  # 'attribute' is not supported by the parent
                return parent.get_style_recursive(attribute, flowable_target)
        except BaseStyleException as exception:
            return self.get_base_style_recursive(exception, flowable_target)

    @cached
    def _style(self, container):
        if isinstance(self.style, Style):
            return self.style
        else:
            return container.document.stylesheet.find_style(self, container)

    def before_placing(self, container):
        pass


class InvalidStyledMatcher(Exception):
    """The :class:`StyledMatcher` includes selectors which reference selectors
    which are not defined."""

    def __init__(self, missing_selectors):
        self.missing_selectors = missing_selectors


class StyledMatcher(dict):
    """Dictionary mapping labels to selectors.

    This matcher can be initialized in the same way as a :class:`python:dict`
    by passing a mapping, an interable and/or keyword arguments.

    """

    def __init__(self, mapping_or_iterable=None, **kwargs):
        super().__init__()
        self.by_name = {}
        self._pending = {}
        self.update(mapping_or_iterable, **kwargs)

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
                    selector = selector.flatten(container)
                    specificity = selector.match(styled, container)
                    if specificity:
                        yield Match(name, specificity)


class StyleSheet(RuleSet, Resource):
    """Dictionary storing a collection of related styles by name.

    :class:`Style`\ s stored in a :class:`StyleSheet` can refer to their base
    style by name.

    Args:
        name (str): a label for this style sheet
        matcher (StyledMatcher): the matcher providing the selectors the styles
            contained in this style sheet map to. If no matcher is given, the
            `base`\ 's matcher is used.
        base (StyleSheet): the style sheet to extend
        description (str): a short string describing this style sheet
        pygments_style (str): the Pygments style to use for styling code blocks

    """

    resource_type = 'stylesheet'

    def __init__(self, name, matcher=None, base=None, description=None,
                 pygments_style=None, **user_options):
        base = self.from_string(base) if isinstance(base, str) else base
        from .highlight import pygments_style_to_stylesheet
        if pygments_style:
            base = pygments_style_to_stylesheet(pygments_style, base)
        super().__init__(base)
        self.name = name
        self.description = description
        self.matcher = matcher if matcher is not None else StyledMatcher()
        self.matcher.check_validity()
        if user_options:
            warn('Unsupported options passed to stylesheet: {}'
                 .format(', '.join(user_options.keys())))
        self.user_options = user_options
        self.variables = {}

    def get_styled(self, name):
        return self.get_selector(name).get_styled_class(self.matcher)

    def get_entry_class(self, name):
        return self.get_styled(name).style_class

    def _get_variable(self, name, accepted_type):
        return self.variables[name]

    def get_selector(self, name):
        try:
            return self.matcher.by_name[name]
        except (AttributeError, KeyError):
            if self.base is not None:
                return self.base.get_selector(name)
            else:
                raise KeyError("No selector found for style '{}'".format(name))

    def find_matches(self, styled, container):
        for match in self.matcher.match(styled, container):
            yield match
        if self.base is not None:
            for match in self.base.find_matches(styled, container):
                yield match

    def find_style(self, styled, container):
        matches = sorted(self.find_matches(styled, container),
                         key=attrgetter('specificity'), reverse=True)
        if len(matches) > 1:
            last_match = matches[0]
            for match in matches[1:]:
                if (match.specificity == last_match.specificity
                        and match.style_name != last_match.style_name):
                    styled.warn('Multiple selectors match with the same '
                                'specificity. See the style log for details.',
                                container)
                last_match = match
        for match in matches:
            try:
                return self[match.style_name]
            except KeyError:
                pass
        raise NoStyleException


class StyleSheetFile(StyleSheet):
    """Loads styles defined in a `.rts` file (INI format).

    Args:
        filename (str): the path to the style sheet file

    :class:`StyleSheetFile` takes the same optional arguments as
    :class:`StyleSheet`.  These can also be specified in the ``[STYLESHEET]``
    section of the style sheet file. If an argument is specified in both
    places, the one passed as an argument overrides the one specified in the
    style sheet file.

    """

    RE_VARIABLE = re.compile(r'^\$\(([a-z_ -]+)\)$', re.IGNORECASE)
    RE_SELECTOR = re.compile(r'^(?P<name>[a-z]+)\((?P<args>.*)\)$', re.I)

    def __init__(self, filename, matcher=None, base=None, **kwargs):
        config = ConfigParser(default_section=None, delimiters=('=',),
                              comment_prefixes=('#', ), interpolation=None)
        with open(filename) as file:
            config.read_file(file)
        options = dict(config['STYLESHEET']
                       if config.has_section('STYLESHEET') else {})
        name = options.pop('name', filename)
        base = options.pop('base', base)
        options.update(kwargs)    # optionally override options
        super().__init__(name, matcher, base, **options)
        self.filename = filename
        if config.has_section('VARIABLES'):
            for name, value in config.items('VARIABLES'):
                self.variables[name] = value
        for section_name, section_body in config.items():
            if section_name in (None, 'STYLESHEET', 'VARIABLES'):
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
                style_cls = self.get_entry_class(style_name)
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


class Specificity(namedtuple('Specificity',
                             ['priority', 'location', 'style', 'attributes',
                              'klass'])):
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


ZERO_SPECIFICITY = Specificity(0, 0, 0, 0, 0)

NO_MATCH = Match(None, ZERO_SPECIFICITY)


class StyleLogEntry(object):
    def __init__(self, styled, container, matches, continued,
                 custom_message=None):
        self.styled = styled
        self.container = container
        self.matches = matches
        self.continued = continued
        self.custom_message = custom_message

    @property
    def page_number(self):
        return self.container.page.formatted_number


class StyleLog(object):
    def __init__(self, stylesheet):
        self.stylesheet = stylesheet
        self.entries = []

    def log_styled(self, styled, container, continued, custom_message=None):
        matches = self.stylesheet.find_matches(styled, container)
        log_entry = StyleLogEntry(styled, container, matches, continued,
                                  custom_message)
        self.entries.append(log_entry)

    def log_out_of_line(self):
        raise NotImplementedError

    def write_log(self, filename_root):
        with open(filename_root + '.stylelog', 'w') as log:
            current_page = None
            current_container = None
            for entry in self.entries:
                if entry.page_number != current_page:
                    current_page = entry.page_number
                    log.write('{line} page {} {line}\n'.format(current_page,
                                                               line='-' * 34))
                container = entry.container
                if container.top_level_container is not current_container:
                    current_container = container.top_level_container
                    log.write("#### {}('{}')\n"
                              .format(type(current_container).__name__,
                                      current_container.name))
                styled = entry.styled
                level = styled.nesting_level
                attrs = OrderedDict()
                style = None
                indent = '  ' * level
                if styled.parent and (styled.source.location
                                      != styled.parent.source.location):
                    location = '   ' + styled.source.location
                else:
                    location = ''
                continued_text = '(continued) ' if entry.continued else ''
                log.write('  {}{}{}{}'
                          .format(indent, continued_text,
                                  styled.short_repr(container), location))
                if entry.custom_message:
                    log.write('\n      {} ! {}\n'.format(indent,
                                                         entry.custom_message))
                    continue
                first = True
                if style is not None:
                    first = False
                    style_attrs = ', '.join(key + '=' + value
                                            for key, value in style.items())
                    log.write('\n      {} > {}({})'
                              .format(indent, attrs['style'], style_attrs))
                matches = sorted(entry.matches, reverse=True,
                                 key=attrgetter('specificity'))
                if matches:
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
                        log.write('\n      {} {} ({}) {}'
                                  .format(indent, label, specificity,
                                          match.style_name))
                    if style is None:
                        log.write('\n      {} > fallback to default style'
                                  .format(indent))
                log.write('\n')
