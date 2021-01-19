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


import string

from ast import literal_eval
from collections import OrderedDict, namedtuple
from contextlib import suppress
from itertools import chain
from operator import attrgetter
from pathlib import Path

from .attribute import (WithAttributes, AttributesDictionary,
                        RuleSet, RuleSetFile, Configurable,
                        DefaultValueException, Attribute, Bool)
from .element import DocumentElement
from .resource import Resource, ResourceNotFound
from .util import (cached, all_subclasses, NotImplementedAttribute,
                   class_property)
from .warnings import warn


__all__ = ['Style', 'Styled', 'StyledMeta',
           'StyledMatcher', 'StyleSheet', 'StyleSheetFile',
           'ClassSelector', 'ContextSelector', 'PARENT_STYLE']


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

    hide = Attribute(Bool, False, 'Suppress rendering this element')

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
        self.name = None

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

    @classmethod
    def get_ruleset(self, document):
        return document.stylesheet


class ParentStyle(Style):
    """Style that forwards attribute lookups to the parent of the
    :class:`Styled` from which the lookup originates."""


PARENT_STYLE = ParentStyle()


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
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def pri(self, priority):
        return SelectorWithPriority(self, priority)

    def get_styled_class(self, stylesheet_or_matcher):
        raise NotImplementedError

    def get_style_name(self, matcher):
        raise NotImplementedError

    @property
    def referenced_selectors(self):
        raise NotImplementedError

    def flatten(self, stylesheet):
        raise NotImplementedError

    def match(self, styled, stylesheet, document):
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

    def flatten(self, stylesheet):
        flattened_selector = self.selector.flatten(stylesheet)
        return flattened_selector.pri(self.priority)

    def match(self, styled, stylesheet, document):
        score = self.selector.match(styled, stylesheet, document)
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

    def flatten(self, stylesheet):
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

    def flatten(self, stylesheet):
        return stylesheet.get_selector(self.name)

    def get_styled_class(self, stylesheet_or_matcher):
        selector = stylesheet_or_matcher.get_selector(self.name)
        return selector.get_styled_class(stylesheet_or_matcher)

    def get_style_name(self, matcher):
        selector = matcher.by_name[self.name]
        return selector.get_style_name(matcher)

    def match(self, styled, stylesheet, document):
        selector = stylesheet.get_selector(self.name)
        return selector.match(styled, stylesheet, document)


class ClassSelectorBase(SingleSelector):
    def get_styled_class(self, stylesheet_or_matcher):
        return self.cls

    @property
    def referenced_selectors(self):
        return
        yield

    def flatten(self, stylesheet):
        return self

    def get_style_name(self, matcher):
        return self.style_name

    def match(self, styled, stylesheet, document):
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
            if not hasattr(styled, attr):
                return None
            attr = getattr(styled, attr)
            if callable(attr):
                attr = attr(document)
            if attr != value:
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

    def flatten(self, stylesheet):
        return type(self)(*(child_selector for selector in self.selectors
                            for child_selector
                            in selector.flatten(stylesheet).selectors))

    def get_styled_class(self, stylesheet_or_matcher):
        return self.selectors[-1].get_styled_class(stylesheet_or_matcher)

    def get_style_name(self, matcher):
        return self.selectors[-1].get_style_name(matcher)

    def match(self, styled, stylesheet, document):
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
                    while not selector.match(element, stylesheet, document):
                        element = next(elements)        # NoMoreParentElement
            except NoMoreParentElement:
                return None
            except StopIteration:
                break
            score = selector.match(element, stylesheet, document)
            if not score:
                return None
            total_score += score
        return total_score


class NoMoreParentElement(Exception):
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

    def match(self, styled, stylesheet):
        location_match = self.location_class.match(styled, stylesheet)
        if location_match:
            match = self.selector.match(styled, stylesheet)
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


class Styled(DocumentElement, Configurable, metaclass=StyledMeta):
    """A document element who's style can be configured.

    Args:
        style (str, Style): the style to associate with this element. If
            `style` is a string, the corresponding style is lookup up in the
            document's style sheet by means of selectors.

    """

    @class_property
    def configuration_class(cls):
        return cls.style_class

    style_class = None
    """The :class:`Style` subclass that corresponds to this :class:`Styled`
    subclass."""

    def __init__(self, id=None, style=None, parent=None, source=None):
        """Associates `style` with this element. If `style` is `None`, an empty
        :class:`Style` is create, effectively using the defaults defined for the
        associated :class:`Style` class).
        A `parent` can be passed on object initialization, or later by
        assignment to the `parent` attribute."""
        super().__init__(id=id, parent=parent, source=source)
        if (isinstance(style, Style)
                and not isinstance(style, (self.style_class, ParentStyle))):
            raise TypeError('the style passed to {} should be of type {} '
                            '(a {} was passed instead)'
                            .format(self.__class__.__name__,
                                    self.style_class.__name__,
                                    style.__class__.__name__))
        self.style = style
        self.classes = []

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

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

    def configuration_name(self, document):
        try:    # TODO: make document hashable so @cached can be used?
            return self._style_name
        except AttributeError:
            ruleset = self.configuration_class.get_ruleset(document)
            self._style_name = ruleset.find_style(self, document)
            return self._style_name

    def fallback_to_parent(self, attribute):
        return isinstance(self.style, ParentStyle)

    @cached
    def get_style(self, attribute, container):
        if isinstance(self.style, Style):
            try:
                return self.style[attribute]
            except KeyError:
                pass
        return self.get_config_value(attribute, container.document)

    @property
    def has_class(self):
        """Filter selection on a class of this :class:`Styled`"""
        return HasClass(self)

    @property
    def has_classes(self):
        """Filter selection on a set of classes of this :class:`Styled`"""
        return HasClasses(self)

    def before_placing(self, container):
        if self.parent:
            self.parent.before_placing(container)


class HasClass(object):
    def __init__(self, styled):
        self.styled = styled

    def __eq__(self, class_name):
        return class_name in self.styled.classes


class HasClasses(object):
    def __init__(self, styled):
        self.styled = styled

    def __eq__(self, class_names):
        return set(class_names).issubset(self.styled.classes)


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
        for referenced_name in set(selector.referenced_selectors):
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

    def match(self, styled, stylesheet, document):
        for cls in type(styled).__mro__:
            if cls not in self:
                continue
            style_str = styled.style if isinstance(styled.style, str) else None
            for style in set((style_str, None)):
                for name, selector in self[cls].get(style, {}).items():
                    selector = selector.flatten(stylesheet)
                    specificity = selector.match(styled, stylesheet, document)
                    if specificity:
                        yield Match(name, specificity)


class StyleSheet(RuleSet, Resource):
    """Dictionary storing a collection of related styles by name.

    :class:`Style`\\ s stored in a :class:`StyleSheet` can refer to their base
    style by name.

    Args:
        name (str): a label for this style sheet
        matcher (StyledMatcher): the matcher providing the selectors the styles
            contained in this style sheet map to. If no matcher is given and
            `base` is specified, the `base`\\ 's matcher is used. If `base` is
            not set, the default matcher is used.
        base (StyleSheet or str): the style sheet to extend
        description (str): a short string describing this style sheet
        pygments_style (str): the Pygments style to use for styling code blocks

    """

    resource_type = 'stylesheet'
    main_section = 'STYLESHEET'
    extension = '.rts'

    def __init__(self, name, matcher=None, base=None, source=None,
                 description=None, pygments_style=None, **user_options):
        from .highlight import pygments_style_to_stylesheet
        from .stylesheets import matcher as default_matcher

        base = self.from_string(base, self) if isinstance(base, str) else base
        if matcher is None:
            matcher = default_matcher if base is None else StyledMatcher()
        if matcher is not None:
            matcher.check_validity()
        if pygments_style:
            base = pygments_style_to_stylesheet(pygments_style, base)
        super().__init__(name, base=base, source=source)
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
    def parse_string(cls, string, source):
        with suppress(ResourceNotFound):
            return super().parse_string(string, source)
        return StyleSheetFile(string, source=source)

    @classmethod
    def doc_repr(cls, value):
        for name, ep in cls.installed_resources:
            if value is ep.load():
                return ('``{}`` (= :data:`{}.{}`)'
                        .format(name, *ep.value.split(':')))
        raise NotImplementedError

    @classmethod
    def doc_format(cls):
        return ('the name of an :ref:`installed style sheet <included_style_'
                'sheets>` or the filename of a stylesheet file (with the '
                '``{}`` extension)'.format(cls.extension))

    def _get_value_lookup(self, styled, attribute, document):
        try:
            return super()._get_value_lookup(styled, attribute, document)
        except DefaultValueException:
            if styled.fallback_to_parent(attribute):
                return self._get_value_lookup(styled.parent, attribute, document)
            raise

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

    def find_matches(self, styled, document):
        for match in self.matcher.match(styled, self, document):
            yield match
        if self.base is not None:
            yield from self.base.find_matches(styled, document)

    def find_style(self, styled, document):
        matches = sorted(self.find_matches(styled, document),
                         key=attrgetter('specificity'), reverse=True)
        last_match = Match(None, ZERO_SPECIFICITY)
        for match in matches:
            if (match.specificity == last_match.specificity
                    and match.style_name != last_match.style_name):
                styled.warn('Multiple selectors match with the same '
                            'specificity. See the style log for details.')
            if self.contains(match.style_name):
                return match.style_name
            last_match = match
        raise DefaultValueException

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
            section['base'] = str(style.base)
            for name in type(style).supported_attributes:
                try:
                    section[name] = str(style[name])
                except KeyError:  # default
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
            try:
                style_cls = self.get_entry_class(style_name)
            except KeyError:
                warn("The style definition '{}' will be ignored since there"
                     " is no selector defined for it in the matcher."
                     .format(style_name))
                return
        self[style_name] = style_cls(**dict(items))


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
            priority = 0
            while chars.peek() in '+-':
                priority += 1 if next(chars) == '+' else -1
            selector = parse_class_selector(chars)
            if priority != 0:
                selector = selector.pri(priority)
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
    if next(chars) != '(':
        raise StyleParseError('Expecting an opening brace')
    eat_whitespace(chars)
    while chars.peek() not in (None, ')'):
        argument, unknown_keyword = parse_value(chars)
        eat_whitespace(chars)
        if chars.peek() == '=':
            next(chars)
            keyword = argument
            if not unknown_keyword:
                raise StyleParseError("'{}' is not a valid keyword argument"
                                      .format(keyword))
            eat_whitespace(chars)
            argument, unknown_keyword = parse_value(chars)
            kwargs[keyword] = argument
        elif kwargs:
            raise StyleParseError('Non-keyword argument cannot follow a '
                                  'keyword argument')
        else:
            args.append(argument)
        if unknown_keyword:
            raise StyleParseError("Unknown keyword '{}'".format(argument))
        eat_whitespace(chars)
        if chars.peek() == ',':
            next(chars)
            eat_whitespace(chars)
    if chars.peek() is None or next(chars) != ')':
        raise StyleParseError('Expecting a closing brace')
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


def parse_value(chars):
    unknown_keyword = False
    first_char = chars.peek()
    if first_char in ("'", '"'):
        value = parse_string(chars)
    elif first_char.isnumeric() or first_char in '+-':
        value = parse_number(chars)
    else:
        value, unknown_keyword = parse_keyword(chars)
    return value, unknown_keyword


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


def parse_keyword(chars):
    keyword = chars.match(string.ascii_letters + string.digits + '_')
    try:
        return KEYWORDS[keyword.lower()], False
    except KeyError:
        return keyword, True


KEYWORDS = dict(true=True, false=False, none=None)


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
        matches = self.stylesheet.find_matches(styled, container.document)
        log_entry = StyleLogEntry(styled, container, matches, continued,
                                  custom_message)
        self.entries.append(log_entry)

    def log_out_of_line(self):
        raise NotImplementedError

    def write_log(self, filename_root):
        stylelog_path = filename_root.with_suffix('.stylelog')
        with stylelog_path.open('w', encoding='utf-8') as log:
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
                location = ('   ' + styled.source.location if styled.source
                            else '')
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
                        if self.stylesheet.contains(match.style_name):
                            if first:
                                name = match.style_name
                                style = self.stylesheet.get_configuration(name)
                                label = '>'
                                first = False
                            else:
                                label = ' '
                        else:
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
