# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from token import LPAR, RPAR

from .attribute import Attribute, ParseError
from .dimension import Dimension, PT
from .element import DocumentElement
from .flowable import Flowable, FlowableStyle
from .layout import VirtualContainer
from .style import StyledMeta
from .text import InlineStyle, InlineStyled
from .util import NotImplementedAttribute


__all__ = ['InlineFlowableException', 'InlineFlowable', 'InlineFlowableStyle']


class InlineFlowableException(Exception):
    pass


class InlineFlowableStyle(FlowableStyle, InlineStyle):
    baseline = Attribute(Dimension, 0*PT, "The location of the flowable's "
                                          "baseline relative to the bottom "
                                          "edge")


class InlineFlowableMeta(StyledMeta):
    def __new__(mcls, classname, bases, cls_dict):
        cls = super().__new__(mcls, classname, bases, cls_dict)
        if classname == 'InlineFlowable':
            cls.directives = {}
        else:
            InlineFlowable.directives[cls.directive] = cls
        return cls


class InlineFlowable(Flowable, InlineStyled, metaclass=InlineFlowableMeta):
    directive = None
    style_class = InlineFlowableStyle
    arguments = NotImplementedAttribute()

    def __init__(self, baseline=None, id=None, style=None, parent=None,
                 source=None):
        super().__init__(id=id, style=style, parent=parent, source=source)
        self.baseline = baseline

    def to_string(self, flowable_target):
        return type(self).__name__

    def font(self, document):
        raise InlineFlowableException

    def y_offset(self, document):
        return 0

    @property
    def items(self):
        return [self]

    @classmethod
    def from_tokens(cls, tokens, source):
        directive = next(tokens).string.lower()
        inline_flowable_class = InlineFlowable.directives[directive]
        if next(tokens).exact_type != LPAR:
            raise ParseError('Expecting an opening parenthesis.')
        args, kwargs = inline_flowable_class.arguments.parse_arguments(tokens,
                                                                       source)
        if next(tokens).exact_type != RPAR:
            raise ParseError('Expecting a closing parenthesis.')
        return inline_flowable_class(*args, source=source, **kwargs)

    def spans(self, document):
        yield self

    def flow_inline(self, container, last_descender, state=None):
        baseline = self.baseline or self.get_style('baseline', container)
        virtual_container = VirtualContainer(container)
        width, _, _ = self.flow(virtual_container, last_descender, state=state)
        return InlineFlowableSpan(width, baseline, virtual_container)


class InlineFlowableSpan(DocumentElement):
    number_of_spaces = 0
    ends_with_space = False

    def __init__(self, width, baseline, virtual_container):
        super().__init__()
        self.width = width
        self.baseline = baseline
        self.virtual_container = virtual_container

    def font(self, document):
        raise InlineFlowableException

    @property
    def span(self):
        return self

    def height(self, document):
        return self.ascender(document) - self.descender(document)

    def ascender(self, document):
        baseline = self.baseline.to_points(self.virtual_container.height)
        if baseline > self.virtual_container.height:
            return 0
        else:
            return self.virtual_container.height - baseline

    def descender(self, document):
        return min(0, - self.baseline.to_points(self.virtual_container.height))

    def line_gap(self, document):
        return 0

    def before_placing(self, container):
        pass

    # TODO: get_style and word_to_glyphs may need proper implementations
    def get_style(self, attribute, document=None):
        pass

    def chars_to_glyphs(self, chars):
        return chars
