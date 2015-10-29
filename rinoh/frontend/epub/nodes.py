# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from . import BodyElement, BodySubElement, InlineElement, GroupingElement

from ... import styleds
from ...annotation import HyperLink, NamedDestination


class Body(BodyElement):
    pass


class Section(GroupingElement):
    grouped_flowables_class = styleds.Section


class Div(GroupingElement):
    grouped_flowables_class = styleds.Section

    RE_SECTION = re.compile(r'sect\d+')

    def build_flowables(self, **kwargs):
        div_class = self.get('class')
        if div_class and self.RE_SECTION.match(div_class):
            return super().build_flowables(**kwargs)
        else:
            return self.children_flowables()


class Img(BodyElement, InlineElement):
    @property
    def image_path(self):
        return self.get('src')

    def build_flowable(self):
        return styleds.Image(self.image_path)

    def build_styled_text(self):
        return styleds.InlineImage(self.image_path)


class P(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(super().process_content())


class H(BodyElement):
    @property
    def in_section(self):
        parent = self.parent
        while not isinstance(parent, Body):
            if isinstance(parent, Section):
                return True
            parent = parent.parent
        return False

    def build_flowable(self):
        if self.in_section:
            try:
                kwargs = dict(custom_label=self.generated.build_styled_text())
            except AttributeError:
                kwargs = dict()
            return styleds.Heading(self.process_content(), **kwargs)
        else:
            return styleds.Paragraph(self.process_content())


class H1(H):
    pass


class H2(H):
    pass


class H3(H):
    pass


class H4(H):
    pass


class Span(InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        text = styleds.MixedStyledText(self.process_content())
        text.classes = self.get('class').split(' ')
        return text


class Em(InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.MixedStyledText(self.process_content(), style='emphasis')


class Strong(InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.MixedStyledText(self.process_content(), style='strong')


class Sup(InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Superscript(self.process_content())


class Sub(InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Subscript(self.process_content())


class Br(BodyElement, InlineElement):
    def build_flowables(self):
        return
        yield

    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Newline()



class Blockquote(GroupingElement):
    style = 'block quote'


class HR(BodyElement):
    def build_flowable(self):
        return styleds.HorizontalRule()


class A(BodyElement, InlineElement):
    def build_styled_text(self, strip_leading_whitespace):
        if self.get('href'):
            annotation = HyperLink(self.get('href'))
            style = 'external link'
        elif self.get('id'):
            annotation = NamedDestination(self.get('id'))
            style = None
        # else:
        #     return styleds.MixedStyledText(self.process_content(),
        #                               style='broken link')
        return styleds.AnnotatedText(self.process_content(), annotation,
                                     style=style)

    def build_flowables(self):
        children = self.getchildren()
        assert len(children) == 0
        return
        yield


class OL(BodyElement):
    def build_flowable(self):
        return styleds.List([item.process() for item in self.li],
                            style='enumerated')


class UL(BodyElement):
    def build_flowable(self):
        return styleds.List([item.process() for item in self.li],
                            style='bulleted')


class LI(BodySubElement):
    def process(self):
        return self.children_flowables()


class DL(BodyElement):
    def build_flowable(self):
        items = [(dt.flowable(), dd.flowable())
                 for dt, dd in zip(self.dt, self.dd)]
        return styleds.DefinitionList(items)


class DT(BodyElement):
    def build_flowable(self):
        term = styleds.Paragraph(self.process_content())
        return styleds.DefinitionTerm([term])


class DD(GroupingElement):
    grouped_flowables_class = styleds.Definition
