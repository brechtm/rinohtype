# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re
import unicodedata

from ... import styleds
from ...dimension import DimensionUnit, PT, INCH, CM, MM, PICA
from ...reference import TITLE, PAGE
from ...text import Superscript

from ..xml.elementtree import Parser

from . import (DITABodyNode, DITABodySubNode, DITAInlineNode, DITAGroupingNode,
               DITADummyNode)


class Map(DITABodyNode):
    def tree(self):
        meta = []
        if 'title' in self.attributes:
            meta.append(styleds.SetMetadataFlowable(title=self.get('title')))
        return meta + self.children_flowables()


class BookMap(Map):
    pass


class BookTitle(DITAGroupingNode):
    pass


class DITASetMetadataNode(DITABodyNode):
    key = None

    def build_flowable(self):
        key = self.key or self.tag_name
        return styleds.SetMetadataFlowable(**{key: self.text})


class BookLibrary(DITASetMetadataNode):
    pass


class MainBookTitle(DITASetMetadataNode):
    key = 'title'


class BookTitleAlt(DITASetMetadataNode):
    pass


class BookMeta(DITAGroupingNode):
    pass


class Author(DITASetMetadataNode):
    pass


class BookID(DITADummyNode):
    pass


class BookRights(DITADummyNode):
    pass


class TopicRef(DITABodyNode):
    def build_flowable(self):
        from . import DITAReader
        reader = DITAReader()
        with open(self.get('href')) as file:
            section = reader.parse(file)
        for child in self.getchildren():
            for flowable in child.flowables():
                section.append(flowable)
        return section


class FrontMatter(DITAGroupingNode):
    pass


class BackMatter(DITAGroupingNode):
    pass


class BookLists(DITADummyNode):
    pass


class BookAbstract(TopicRef):
    def flowables(self):
        yield styleds.AddToFrontMatter(super().flowables())


class Notices(TopicRef):
    pass


class Preface(TopicRef):
    pass


class Chapter(TopicRef):
    pass


class Appendix(TopicRef):
    pass


class Concept(DITAGroupingNode):
    grouped_flowables_class = styleds.Section

    def tree(self):
        section, = self.flowables()
        return section


class ConBody(DITAGroupingNode):
    pass


class Task(DITAGroupingNode):
    grouped_flowables_class = styleds.Section

    def tree(self):
        section, = self.flowables()
        return section


class Topic(Task):
    pass


class Body(DITAGroupingNode):
    pass


class ShortDesc(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content(), style='shortdesc')


class TaskBody(DITAGroupingNode):
    pass


class Context(DITAGroupingNode):
    pass


class Section(DITAGroupingNode):
    style = 'section'


class P(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())


class Title(DITABodyNode):
    def build_flowable(self):
        content = self.process_content()
        if isinstance(self.parent, Section):
            return styleds.Paragraph(content, style='section title')
        else:
            return styleds.Heading(content)


class Steps(DITABodyNode):
    style = 'steps'

    def build_flowables(self):
        try:
            for flowable in self.stepsection.flowables():
                yield flowable
        except AttributeError:
            pass
        yield styleds.List([step.process() for step in self.step],
                           style=self.style)


class Steps_Unordered(Steps):
    style = 'unordered steps'


class StepSection(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())


class Step(DITABodySubNode):
    def process(self):
        return self.children_flowables()


class SubSteps(DITABodyNode):
    style = 'substeps'

    def build_flowables(self):
        try:
            for flowable in self.stepsection.flowables():
                yield flowable
        except AttributeError:
            pass
        yield styleds.List([step.process() for step in self.substep],
                           style=self.style)


class SubStep(Step):
    pass


class Cmd(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content(), style='command')


class CmdName(DITAInlineNode):
    style = 'command name'


class StepResult(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content(), style='step result')


class Info(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content(), style='info')


class Result(DITAGroupingNode):
    pass


class Related_Links(DITAGroupingNode):
    def build_flowables(self, **kwargs):
        concepts = []
        tasks = []
        for link in self.link:
            if link.get('type') == 'concept':
                for flowable in link.flowables():
                    concepts.append(flowable)
            elif link.get('type') == 'task':
                for flowable in link.flowables():
                    tasks.append(flowable)
            else:
                raise NotImplementedError
        items = []
        if concepts:
            label = styleds.Paragraph('Related concepts')
            items.append((styleds.DefinitionTerm([label]),
                          styleds.Definition(concepts)))
        if tasks:
            label = styleds.Paragraph('Related tasks')
            items.append((styleds.DefinitionTerm([label]),
                          styleds.Definition(tasks)))
        yield styleds.DefinitionList(items)


class Link(DITABodyNode):
    def build_flowable(self):
        xml_path = self.node._root._roottree._filename
        target_path = os.path.join(os.path.dirname(xml_path), self.get('href'))
        parser = Parser(None)
        xml_tree = parser.parse(target_path)
        target_id = xml_tree.getroot().get('id')
        section_ref = styleds.Reference(target_id, type=TITLE)
        page_ref = styleds.Reference(target_id, type=PAGE)
        return styleds.Paragraph(section_ref + ' on page ' + page_ref)


RE_LENGTH_PERCENT_UNITLESS = re.compile(r'^(?P<value>\d+)(?P<unit>[a-z%]*)$')

PIXEL = DimensionUnit(1 / 100 * INCH)

DOCUTILS_UNIT_TO_DIMENSION = {'': PIXEL,
                              'pc': PICA,
                              'pt': PT,
                              'px': PIXEL,
                              'in': INCH,
                              'cm': CM,
                              'mm': MM,
                              'em': None}


def convert_quantity(quantity_string):
    if quantity_string is None:
        return None
    value, unit = RE_LENGTH_PERCENT_UNITLESS.match(quantity_string).groups()
    return float(value) * DOCUTILS_UNIT_TO_DIMENSION[unit]


class Image(DITABodyNode, DITAInlineNode):
    @property
    def image_path(self):
        href = self.get('href')
        xml_path = self.node._root._roottree._filename
        return os.path.normcase(os.path.join(os.path.dirname(xml_path), href))

    @property
    def arguments(self):
        # height = convert_quantity(self.get('height'))
        width = convert_quantity(self.get('width'))
        scale = self.get('scale', 100) / 100
        return dict(width=width, scale=scale)

    def build_flowable(self):
        return styleds.Image(self.image_path, **self.arguments)

    def build_styled_text(self, strip_leading_whitespace):
        return styleds.InlineImage(self.image_path, **self.arguments)


class UL(DITABodyNode):
    def build_flowable(self):
        return styleds.List([list(item.flowables()) for item in self.li],
                            style='enumerated')


class LI(DITAGroupingNode):
    def build_flowables(self, **kwargs):
        if self.text:
            yield styleds.Paragraph(self.process_content())
        for flowable in self.children_flowables():
            yield flowable


class SL(DITABodyNode):
    def build_flowable(self):
        return styleds.List([list(item.flowables()) for item in self.sli],
                            style='simple')


class SLI(P):
    pass


class TM(DITAInlineNode):
    style = 'trademark'

    SYMBOLS = {'tm': unicodedata.lookup('TRADE MARK SIGN'),
               'reg': Superscript(unicodedata.lookup('REGISTERED SIGN')),
               'service': unicodedata.lookup('SERVICE MARK')}

    def build_styled_text(self, strip_leading_whitespace=False):
        tmtype = self.get('tmtype')
        text = super().build_styled_text(strip_leading_whitespace)
        return text + self.SYMBOLS[tmtype]


class Prolog(DITADummyNode):
    pass


class Prereq(DITAGroupingNode):
    style = 'prerequisites'


class Note(DITAGroupingNode):
    def build_flowable(self):
        grouped_flowables = super().build_flowable()
        note_type = self.get('type', 'note')
        return styleds.Framed(grouped_flowables, style=note_type)


class TutorialInfo(DITABodyNode):
    def build_flowable(self):
        return styleds.Paragraph(self.process_content())
