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


from collections import OrderedDict

from .element import DocumentElement
from .util import cached


__all__ = ['Style', 'Styled', 'Var',
           'StyledMatcher', 'StyleSheet', 'ClassSelector', 'ContextSelector',
           'PARENT_STYLE', 'StyleException']


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


class Style(dict):
    """"Dictionary storing style attributes.

    Attrributes can also be accessed as attributes."""

    attributes = {}
    """Dictionary holding the supported style attributes for this :class:`Style`
    class (keys) and their default values (values)"""

    default_base = None

    def __init__(self, base=None, **attributes):
        """Style attributes are as passed as keyword arguments. Supported
        attributes include those defined in the :attr:`attributes` attribute of
        this style class and those defined in style classes this one inherits
        from.

        Optionally, a `base` (:class:`Style`) is passed, where attributes are
        looked up when they have not been specified in this style.
        Alternatively, if `base` is :class:`PARENT_STYLE`, the attribute lookup
        is forwarded to the parent of the element the lookup originates from.
        If `base` is a :class:`str`, it is used to look up the base style in
        the :class:`StyleStore` this style is stored in."""
        self.base = base or self.default_base
        self.name = None
        self.stylesheet = None
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        super().__init__(attributes)

    def __repr__(self):
        """Return a textual representation of this style."""
        return '{0}({1}) > {2}'.format(self.__class__.__name__, self.name or '',
                                       self.base)

    def __copy__(self):
        copy = self.__class__(base=self.base, **self)
        if self.name is not None:
            copy.name = self.name + ' (copy)'
            copy.stylesheet = self.stylesheet
        return copy

    def __getattr__(self, attribute):
        if attribute in self._supported_attributes():
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
            for super_cls in cls.__mro__:
                if attribute in super_cls.attributes:
                    return super_cls.attributes[attribute]
        except AttributeError:
            raise KeyError("No attribute '{}' in {}".format(attribute, cls))

    @classmethod
    def _supported_attributes(cls):
        """Return a :class:`set` of the attributes supported by this style
        class."""
        attributes = set()
        try:
            for super_cls in cls.__mro__:
                attributes.update(super_cls.attributes.keys())
        except AttributeError:
            return attributes

    def get_value(self, attribute, document):
        value = self[attribute]
        if isinstance(value, VarBase):
            value = value.get(document)
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
    cls = None

    def __truediv__(self, other):
        try:
            selectors = self.selectors + other.selectors
        except AttributeError:
            assert other == Ellipsis
            selectors = self.selectors + (other, )
        return ContextSelector(*selectors)

    def match(self, styled):
        raise NotImplementedError


class ClassSelectorBase(Selector):
    @property
    def selectors(self):
        return (self, )

    def match(self, styled):
        class_match = 2 if type(styled) == self.cls else 1
        attributes_result = style_name_result = None
        if self.attributes:
            for attr, value in self.attributes.items():
                if not hasattr(styled, attr) or getattr(styled, attr) != value:
                    attributes_result = False
                    break
            else:
                attributes_result = True
        if self.style_name is not None:
            style_name_result = styled.style == self.style_name
        if False in (attributes_result, style_name_result):
            return None
        else:
            return Specificity(style_name_result or False,
                               attributes_result or False, class_match)


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
    def cls(self):
        return self.selectors[-1].cls

    @property
    def style_name(self):
        return self.selectors[-1].style_name

    def match(self, styled):
        total_score = ZERO_SPECIFICITY
        selectors = reversed(self.selectors)
        selector = next(selectors)
        while True:
            if styled is None:
                return None
            if selector is Ellipsis:
                selector = next(selectors)
                while True:
                    if selector.match(styled):
                        break
                    styled = styled.parent
                    if styled is None:
                        return None
            if not isinstance(styled, selector.cls):
                return None
            score = selector.match(styled)
            if not score:
                return None
            total_score += score
            styled = styled.parent
            try:
                selector = next(selectors)
            except StopIteration:
                break
        return total_score


class StyledMeta(type, ClassSelectorBase):
    attributes = None
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

    def __init__(self, style=None, parent=None):
        """Associates `style` with this element. If `style` is `None`, an empty
        :class:`Style` is create, effectively using the defaults defined for the
        associated :class:`Style` class).
        A `parent` can be passed on object initialization, or later by
        assignment to the `parent` attribute."""
        super().__init__(parent=parent)
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

    @cached
    def get_style(self, attribute, document=None):
        try:
            return self.get_style_recursive(attribute, document)
        except DefaultStyleException:
            # self.warn('Falling back to default style for ({})'
            #           .format(self.path))
            return self.style_class._get_default(attribute)

    def get_base_style_recursive(self, exception, document):
        try:
            base_style = document.stylesheet[exception.base_name]
            return base_style.get_value(exception.attribute, document)
        except ParentStyleException:
            return self.parent.get_style_recursive(exception.attribute,
                                                   document)
        except BaseStyleException as e:
            return self.get_base_style_recursive(e, document)

    def get_style_recursive(self, attribute, document=None):
        try:
            try:
                style = self._style(document)
                return style.get_value(attribute, document)
            except DefaultStyleException:
                if self.style_class.default_base == PARENT_STYLE:
                    raise ParentStyleException
                raise
        except ParentStyleException:
            return self.parent.get_style_recursive(attribute, document)
        except BaseStyleException as exception:
            return self.get_base_style_recursive(exception, document)

    @cached
    def _style(self, document):
        if isinstance(self.style, Style):
            return self.style
        else:
            return document.stylesheet.find_style(self)
        raise DefaultStyleException


class AmbiguousStyleSheetException(Exception):
    pass


class StyledMatcher(dict):
    def __init__(self):
        self.by_name = {}

    def __call__(self, name, selector):
        self[name] = selector

    def __setitem__(self, name, selector):
        assert name not in self
        style_selectors, cls_selectors = self.setdefault(selector.cls, ([], []))
        if selector.style_name:
            style_selectors.append((name, selector))
        else:
            cls_selectors.append((name, selector))
        self.by_name[name] = selector

    def best_match(self, styled):
        scores = {}
        for cls in type(styled).__mro__:
            if cls not in self:
                continue
            style_selectors, cls_selectors = self[cls]
            selectors = style_selectors if styled.style else cls_selectors
            for name, selector in selectors:
                score = selector.match(styled)
                if score:
                    if score in scores:
                        raise AmbiguousStyleSheetException(name, scores[score])
                    scores[score] = name
        try:
            max_score = max(scores)
            return Match(scores[max_score], max_score)
        except ValueError:
            return NO_MATCH


class StyleSheet(OrderedDict):
    """Dictionary storing a set of related :class:`Style`s by name.

    :class:`Style`s stored in a :class:`StyleStore` can refer to their base
    style by name. See :class:`Style`."""

    def __init__(self, name, matcher=None, base=None):
        super().__init__()
        self.name = name
        self.matcher = matcher or base.matcher
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
        style.stylesheet = self
        super().__setitem__(name, style)

    def __call__(self, name, **kwargs):
        selector = self.matcher.by_name[name]
        self[name] = selector.cls.style_class(**kwargs)

    def get_variable(self, name):
        try:
            return self.variables[name]
        except KeyError:
            return self.base.get_variable(name)

    def find_best_match(self, styled):
        try:
            best_match = self.matcher.best_match(styled)
        except AttributeError:
            best_match = NO_MATCH
        if self.base:
            base_best_match = self.base.find_best_match(styled)
            if base_best_match > best_match:
                best_match = base_best_match
        return best_match

    def find_style(self, styled):
        match = self.find_best_match(styled)
        if match:
            # print("({}) matches '{}'".format(styled.path, match.style_name))
            try:
                return self[match.style_name]
            except KeyError:
                print("No style '{}' found in stylesheet"
                      .format(match.style_name))
        raise DefaultStyleException


class VarBase(object):
    def __getattr__(self, name):
        return VarAttribute(self, name)

    def get(self, document):
        raise NotImplementedError


class Var(VarBase):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def get(self, document):
        return document.get_style_var(self.name)


class VarAttribute(VarBase):
    def __init__(self, parent, attribute_name):
        super().__init__()
        self.parent = parent
        self.attribute_name = attribute_name

    def get(self, document):
        return getattr(self.parent.get(document), self.attribute_name)


class Specificity(tuple):
    def __new__(cls, *items):
        return super().__new__(cls, items)

    def __add__(self, other):
        return tuple(a + b for a, b in zip(self, other))

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


ZERO_SPECIFICITY = Specificity(0, 0, 0)

NO_MATCH = Match(None, ZERO_SPECIFICITY)
