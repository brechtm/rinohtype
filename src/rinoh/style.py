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

import os
import string

from ast import literal_eval
from collections import OrderedDict, namedtuple
from itertools import chain
from operator import attrgetter

from .attribute import (WithAttributes, AttributesDictionary,
                        RuleSet, RuleSetFile)
from .element import DocumentElement
from .resource import Resource
from .util import cached, unique, all_subclasses, NotImplementedAttribute
from .warnings import warn


__all__ = ['Style', 'Styled', 'StyledMatcher', 'StyleSheet', 'StyleSheetFile',
           'ClassSelector', 'ContextSelector', 'PARENT_STYLE',
           'StyleException']


class StyleException(Exception):
    """Style lookup requires special handling."""


class ParentStyleException(StyleException):
    """Style attribute not found. Consult the parent :class:`Styled`."""


class BaseStyleException(StyleException):
    """The `attribute` is not specified in this :class:`Style`. Try to find the
    attribute in a base style instead."""

    def __init__(self, style, attribute):
        self.style = style
        self.attribute = attribute


class DefaultStyleException(StyleException):
    """The attribute is not specified in this :class:`Style` or any of its base
    styles. Return the default value for the attribute."""


class NoStyleException(StyleException):
    """No style matching the given :class:`Styled` was found in the
    :class:`StyleSheet`."""


class StyleMeta(WithAttributes):
    def __new__(mcls, classname, bases, cls_dict):
        if '__doc__' not in cls_dict:
            styled_class_name = classname.replace('Style', '')
            cls_dict['__doc__'] = ('Style class for :class:`.{}`'
                                   .format(styled_class_name))
        return super().__new__(mcls, classname, bases, cls_dict)


class Style(AttributesDictionary, metaclass=StyleMeta):
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
        self._name = None

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
            if isinstance(self.base, Style):
                return self.base[attribute]
            else:
                raise BaseStyleException(self, attribute)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name in SPECIAL_STYLES:
            raise ValueError("The '{}' style name is reserved.".format(name))
        self._name = name


class SpecialStyle(Style):
    """Special style that delegates attribute lookups by raising an
    exception on each attempt to access an attribute."""

    exception = NotImplementedAttribute()

    def __repr__(self):
        return self.__class__.__name__

    def __getitem__(self, attribute):
        raise self.exception

    def __bool__(self):
        return True


class ParentStyle(SpecialStyle):
    exception = ParentStyleException


class DefaultStyle(SpecialStyle):
    exception = DefaultStyleException


PARENT_STYLE = ParentStyle()
"""Style that forwards style lookups to the parent of the :class:`Styled`
from which the lookup originates."""


DEFAULT_STYLE = DefaultStyle()
"""Style to use as a base for styles that do not extend the style of the same
name in the base style sheet."""


SPECIAL_STYLES = dict(DEFAULT_STYLE=DEFAULT_STYLE,
                      PARENT_STYLE=PARENT_STYLE)


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

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def pri(self, priority):
        return SelectorWithPriority(self, priority)

    def get_styled_class(self, stylesheet_or_matcher):
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

    def get_styled_class(self, stylesheet_or_matcher):
        return self.selector.get_styled_class(stylesheet_or_matcher)

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

    def get_styled_class(self, stylesheet_or_matcher):
        selector = stylesheet_or_matcher.get_selector(self.name)
        return selector.get_styled_class(stylesheet_or_matcher)

    def get_style_name(self, matcher):
        selector = matcher.by_name[self.name]
        return selector.get_style_name(matcher)

    def match(self, styled, container):
        selector = container.document.stylesheet.get_selector(self.name)
        return selector.match(styled, container)


class ClassSelectorBase(SingleSelector):
    def get_styled_class(self, stylesheet_or_matcher):
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

    def get_styled_class(self, stylesheet_or_matcher):
        return self.selectors[-1].get_styled_class(stylesheet_or_matcher)

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

    def __hash__(self):
        return hash(id(self))

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

    def get_base_style_recursive(self, exception, flowable_target, stylesheet):
        base_name = exception.style.base
        if base_name is None:
            stylesheet = stylesheet.base
            if stylesheet is None:
                raise DefaultStyleException
            try:
                base_style = stylesheet[exception.style.name]
            except KeyError:
                raise DefaultStyleException
        else:
            try:
                base_style = stylesheet[base_name]
            except KeyError:
                raise ValueError("The base style '{}' for style '{}' could "
                                 "not be found in the style sheet or base "
                                 "style sheets".format(base_name,
                                                       exception.style.name))
        try:
            return base_style.get_value(exception.attribute, stylesheet)
        except ParentStyleException:
            return self.parent.get_style_recursive(exception.attribute,
                                                   flowable_target)
        except BaseStyleException as exc:
            return self.get_base_style_recursive(exc, flowable_target,
                                                 stylesheet)

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
            return self.get_base_style_recursive(exception, flowable_target,
                                                 stylesheet)

    @cached
    def _style(self, container):
        if isinstance(self.style, Style):
            return self.style
        else:
            return container.document.stylesheet.find_style(self, container)

    def before_placing(self, container):
        if self.parent:
            self.parent.before_placing(container)


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
        self.by_name = OrderedDict()
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

    def get_selector(self, name):
        return self.by_name[name]

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
            contained in this style sheet map to. If no matcher is given and
            `base` is specified, the `base`\ 's matcher is used. If `base` is
            not set, the default matcher is used.
        base (StyleSheet or str): the style sheet to extend
        description (str): a short string describing this style sheet
        pygments_style (str): the Pygments style to use for styling code blocks

    """

    resource_type = 'stylesheet'
    main_section = 'STYLESHEET'
    extension = '.rts'

    def __init__(self, name, matcher=None, base=None, description=None,
                 pygments_style=None, **user_options):
        from .highlight import pygments_style_to_stylesheet
        from .stylesheets import matcher as default_matcher

        base = self.from_string(base) if isinstance(base, str) else base
        if matcher is None:
            matcher = default_matcher if base is None else StyledMatcher()
        if matcher is not None:
            matcher.check_validity()
        if pygments_style:
            base = pygments_style_to_stylesheet(pygments_style, base)
        super().__init__(name, base=base)
        self.description = description
        self.matcher = matcher
        if user_options:
            warn('Unsupported options passed to stylesheet: {}'
                 .format(', '.join(user_options.keys())))
        self.user_options = user_options

    def __str__(self):
        for name, entry_point in self.installed_resources:
            if self is entry_point.load():
                return name
        raise NotImplementedError

    @classmethod
    def parse_string(cls, filename_or_resource_name):
        if os.path.isfile(filename_or_resource_name):
            return StyleSheetFile(filename_or_resource_name)
        else:
            return super().parse_string(filename_or_resource_name)

    @classmethod
    def doc_repr(cls, value):
        for name, entry_point in cls.installed_resources:
            if value is entry_point.load():
                object_name, = entry_point.attrs
                return ('``{}`` (= :data:`{}.{}`)'
                        .format(name, entry_point.module_name, object_name))
        raise NotImplementedError

    @classmethod
    def doc_format(cls):
        return ('the name of an :ref:`installed style sheet <included_style_'
                'sheets>` or the filename of a stylesheet file (with the '
                '``{}`` extension)'.format(cls.extension))

    def get_styled(self, name):
        return self.get_selector(name).get_styled_class(self)

    def get_entry_class(self, name):
        return self.get_styled(name).style_class

    def get_selector(self, name):
        """Find a selector mapped to a style in this or a base style sheet.

        Args:
            name (str): a style name

        Returns:
            :class:`.Selector`: the selector mapped to the style `name`

        Raises:
            KeyError: if the style `name` was not found in this or a base
                style sheet

        """

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

    def write(self, base_filename):
        from configparser import ConfigParser
        config = ConfigParser(interpolation=None)
        config.add_section(self.main_section)
        main = config[self.main_section]
        main['name'] = self.name
        main['description'] = self.description or ''

        config.add_section('VARIABLES')
        variables = config['VARIABLES']
        for name, value in self.variables.items():
            variables[name] = str(value)

        for style_name, style in self.items():
            classifier = ('' if style_name in self.matcher.by_name
                          else ':' + type(style).__name__.replace('Style', ''))
            config.add_section(style_name + classifier)
            section = config[style_name + classifier]
            if style.base is not style.default_base:
                section['base'] = str(style.base)
            for name in type(style).supported_attributes:
                try:
                    section[name] = str(style[name])
                except StyleException:  # default
                    section[';' + name] = str(style._get_default(name))
        with open(base_filename + self.extension, 'w') as file:
            config.write(file, space_around_delimiters=True)
            print(';Undefined styles:', file=file)
            for style_name, selector in self.matcher.by_name.items():
                if style_name in self:
                    continue
                print(';[{}]'.format(style_name), file=file)


class StyleSheetFile(RuleSetFile, StyleSheet):
    """Loads styles defined in a `.rts` file (INI format).

    Args:
        filename (str): the path to the style sheet file

    :class:`StyleSheetFile` takes the same optional arguments as
    :class:`StyleSheet`.  These can also be specified in the ``[STYLESHEET]``
    section of the style sheet file. If an argument is specified in both
    places, the one passed as an argument overrides the one specified in the
    style sheet file.

    """

    def process_section(self, style_name, selector, items):
        if selector:
            selector = parse_selector(selector)
            styled_class = selector.get_styled_class(self)
            if not isinstance(selector, StyledMeta):
                self.matcher[style_name] = selector
            try:
                matcher_styled = self.get_styled(style_name)
                if styled_class is not matcher_styled:
                    raise TypeError("The type '{}' specified for style "
                                    "'{}' does not match the type '{}' "
                                    "returned by the matcher. Note that "
                                    "you do not have to specify the type "
                                    "in this case!"
                                    .format(selector.__name__,
                                            style_name,
                                            matcher_styled.__name__))
            except KeyError:
                pass
            style_cls = styled_class.style_class
        else:
            style_cls = self.get_entry_class(style_name)
        attribute_values = {name: SPECIAL_STYLES.get(val.strip(), val.strip())
                                  if name == 'base' else val
                            for name, val in items}
        self[style_name] = style_cls(**attribute_values)


class StyleParseError(Exception):
    pass


def parse_selector(string):
    chars = CharIterator(string)
    selectors = []
    while True:
        eat_whitespace(chars)
        first_char = chars.peek()
        if first_char in ("'", '"'):
            selector_name = parse_string(chars)
            selector = SelectorByName(selector_name)
        elif first_char == '.':
            assert next(chars) + next(chars) + next(chars) == '...'
            selector = EllipsisSelector()
        else:
            selector = parse_class_selector(chars)
        selectors.append(selector)
        eat_whitespace(chars)
        try:
            next(chars) == '/'
        except StopIteration:
            break
    if len(selectors) == 1:
        return selectors[0]
    else:
        return ContextSelector(*selectors)


def parse_class_selector(chars):
    styled_chars = []
    eat_whitespace(chars)
    while chars.peek() and chars.peek() in string.ascii_letters:
        styled_chars.append(next(chars))
    has_args = chars.peek() == '('
    styled_name = ''.join(styled_chars)
    for selector in all_subclasses(Styled):
        if selector.__name__ == styled_name:
            break
    else:
        raise TypeError("Invalid styled class '{}'".format(styled_name))
    if has_args:
        args, kwargs = parse_selector_args(chars)
        selector = selector.like(*args, **kwargs)
    return selector


def parse_selector_args(chars):
    args, kwargs = [], {}
    assert next(chars) == '('
    eat_whitespace(chars)
    while chars.peek() not in (None, ')'):
        argument = parse_value(chars)
        if argument is not None:
            assert not kwargs
            args.append(argument)
        else:
            keyword = parse_keyword(chars)
            eat_whitespace(chars)
            kwargs[keyword] = parse_value(chars)
        eat_whitespace(chars)
        char = next(chars)
        if char == ')':
            break
        assert char == ','
        eat_whitespace(chars)
    else:
        assert next(chars) == ')'
    return args, kwargs


def eat_whitespace(chars):
    while chars.peek() and chars.peek() in ' \t':
        next(chars)


class CharIterator(str):
    def __init__(self, string):
        self.next_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        index = self.next_index
        self.next_index += 1
        try:
            return self[index]
        except IndexError:
            raise StopIteration

    def match(self, chars):
        """Return all next characters that are listed in `chars` as a string"""
        start_index = self.next_index
        for char in self:
            if char not in chars:
                self.next_index -= 1
                break
        return self[start_index:self.next_index]

    def peek(self):
        try:
            return self[self.next_index]
        except IndexError:
            return None


def parse_keyword(chars):
    keyword = chars.match(string.ascii_letters + string.digits + '_')
    eat_whitespace(chars)
    if chars.peek() != '=':
        raise StyleParseError('Expecting an equals sign to follow a keyword')
    next(chars)
    return keyword


def parse_value(chars):
    first_char = chars.peek()
    if first_char in ("'", '"'):
        value = parse_string(chars)
    elif first_char.isnumeric() or first_char in '+-':
        value = parse_number(chars)
    else:
        value = None
    return value


def parse_string(chars):
    open_quote = next(chars)
    assert open_quote in '"\''
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


def parse_number(chars):
    return literal_eval(chars.match('0123456789.e+-'))


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
        with open(filename_root + '.stylelog', 'w', encoding='utf-8') as log:
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
