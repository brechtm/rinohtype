# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from ... import styleds
from ...annotation import HyperLink, NamedDestination

from . import EPubInlineNode, EPubBodyNode, EPubGroupingNode


class Body(EPubBodyNode):
    pass


class Section(EPubGroupingNode):
    grouped_flowables_class = styleds.Section


class Div(EPubGroupingNode):
    grouped_flowables_class = styleds.Section

    RE_SECTION = re.compile(r'sect\d+')

    def build_flowables(self, **kwargs):
        div_class = self.get('class')
        if div_class and self.RE_SECTION.match(div_class):
            return super().build_flowables(**kwargs)
        else:
            return self.children_flowables()


class Img(EPubBodyNode, EPubInlineNode):
    @property
    def image_path(self):
        return self.get('src')

    def build_flowable(self):
        return styleds.Image(self.image_path)

    def build_styled_text(self, strip_leading_whitespace=False):
        return styleds.InlineImage(self.image_path)


class P(EPubBodyNode):
    def build_flowable(self):
        return styleds.Paragraph(super().process_content())


class H(EPubBodyNode):
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


class Span(EPubInlineNode):
    def build_styled_text(self, strip_leading_whitespace):
        text = styleds.MixedStyledText(self.process_content())
        text.classes = self.get('class').split(' ')
        return text


class Em(EPubInlineNode):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.MixedStyledText(self.process_content(), style='emphasis')


class Strong(EPubInlineNode):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.MixedStyledText(self.process_content(), style='strong')


class Sup(EPubInlineNode):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Superscript(self.process_content())


class Sub(EPubInlineNode):
    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Subscript(self.process_content())


class Br(EPubBodyNode, EPubInlineNode):
    def build_flowables(self):
        return
        yield

    def build_styled_text(self, strip_leading_whitespace):
        return styleds.Newline()



class Blockquote(EPubGroupingNode):
    style = 'block quote'


class HR(EPubBodyNode):
    def build_flowable(self):
        return styleds.HorizontalRule()


class A(EPubBodyNode, EPubInlineNode):
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


class OL(EPubBodyNode):
    def build_flowable(self):
        return styleds.List([item.flowable() for item in self.li],
                            style='enumerated')


class UL(EPubBodyNode):
    def build_flowable(self):
        return styleds.List([item.flowable() for item in self.li],
                            style='bulleted')


class LI(EPubGroupingNode):
    pass


class DL(EPubBodyNode):
    def build_flowable(self):
        items = [(dt.flowable(), dd.flowable())
                 for dt, dd in zip(self.dt, self.dd)]
        return styleds.DefinitionList(items)


class DT(EPubBodyNode):
    def build_flowable(self):
        term = styleds.Paragraph(self.process_content())
        return styleds.DefinitionTerm([term])


class DD(EPubGroupingNode):
    grouped_flowables_class = styleds.Definition
