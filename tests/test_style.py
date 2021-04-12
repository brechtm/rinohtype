# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.attribute import Var
from rinoh.color import HexColor
from rinoh.dimension import PT, CM
from rinoh.document import DocumentTree, Document, FakeContainer
from rinoh.flowable import GroupedFlowables, StaticGroupedFlowables
from rinoh.font import FontWeight, FontSlant, FontWidth
from rinoh.language import EN
from rinoh.paragraph import Paragraph, ParagraphStyle
from rinoh.text import StyledText, SingleStyledText
from rinoh.style import StyleSheet, StyledMatcher, PARENT_STYLE, NEXT_STYLE

emphasis_selector = StyledText.like('emphasis')
emphasis2_selector = StyledText.like('emphasis2')
highlight_selector = StyledText.like('highlight')
highlight2_selector = StyledText.like('highlight2')
paragraph_selector = Paragraph
paragraph2_selector = Paragraph.like('paragraph2')
paragraph3_selector = Paragraph.like('paragraph3')
paragraph4_selector = Paragraph.like('paragraph4')
grouped1_selector = GroupedFlowables.like('grouped1')
paragraph6_selector = grouped1_selector / Paragraph
paragraph7_selector = grouped1_selector / Paragraph.like('paragraph7')
missing_selector = Paragraph.like('missing')

matcher = StyledMatcher({
    'emphasized text': emphasis_selector,
    'emphasized text 2': emphasis2_selector,
    'highlighted text': highlight_selector,
    'highlighted text 2': highlight2_selector,
    'paragraph': paragraph_selector,
    'paragraph 2': paragraph2_selector,
    'paragraph 4': paragraph4_selector,
    'grouped 1': grouped1_selector,
    'paragraph 6': paragraph6_selector,
    'missing style': missing_selector,
})

ssheet1 = StyleSheet('ssheet1', matcher)

ssheet1.variables['font-size'] = 5*PT
ssheet1.variables['text-align'] = 'center'
ssheet1.variables['font-color'] = HexColor('f00')

ssheet1('emphasized text',
        font_slant='italic',
        font_size=Var('font-size'))
ssheet1('emphasized text 2',
        base='emphasized text',
        font_slant='oblique')
ssheet1('highlighted text',
        font_color=HexColor('00f'))
ssheet1('highlighted text 2',
        base='highlighted text',
        font_size=12*PT)
ssheet1('paragraph',
        margin_right=55*PT,
        space_above=5*PT,
        text_align=Var('text-align'),
        font_size=8*PT,
        font_color=Var('font-color'),
        indent_first=2*PT)
ssheet1('paragraph 2',
        padding_bottom=3*PT)
ssheet1('paragraph 4',
        base='paragraph',
        padding_top=5*PT,
        before=SingleStyledText('before p4'))
ssheet1('grouped 1',
        padding_top=3*PT)
ssheet1('paragraph 6',
        base=NEXT_STYLE,
        space_above=6*PT)



matcher2 = StyledMatcher({
    'paragraph 3': paragraph3_selector,
    'paragraph 7': paragraph7_selector,
})

ssheet2 = StyleSheet('ssheet2', base=ssheet1, matcher=matcher2)

ssheet2.variables['font-size'] = 20*PT
ssheet2.variables['text-align'] = 'right'
ssheet2.variables['indent-first'] = 0.5*CM

ssheet2('highlighted text',
        font_slant='italic')
ssheet2('paragraph',
        space_below=10*PT,
        indent_first=Var('indent-first'),
        font_width='condensed')
ssheet2('paragraph 3',
        base='paragraph 2',
        margin_left=1*PT)
ssheet2['paragraph 4'] = ParagraphStyle(padding_right=2*PT,
                                        after=SingleStyledText('after p4'))
ssheet2('paragraph 7',
        base=PARENT_STYLE,
        margin_left=7*PT)


highlighted = SingleStyledText('highlighed', style='highlight')
highlighted2 = SingleStyledText('highlighed 2', style='highlight2')
emphasized = SingleStyledText('emphasized', style='emphasis')
emphasized2 = SingleStyledText('emphasized 2', style='emphasis2')
paragraph = Paragraph('A paragraph with ' + emphasized + ' text.')
paragraph2 = Paragraph('A second paragraph with ' + emphasized2 + ' text.',
                       style='paragraph2')
emphasized3 = SingleStyledText('emphasized 3', style='emphasis2')
paragraph3 = Paragraph('A third paragraph with ' + emphasized3 + ' text.',
                       style='paragraph3')
paragraph4 = Paragraph('A fourth paragraph.', style='paragraph4')
paragraph5 = Paragraph('A paragraph for which no style is present in the '
                       'style sheet', style='missing')
paragraph6 = Paragraph('A sixth paragraph with ' + highlighted + ' text.')
paragraph7 = Paragraph('A seventh paragraph with ' + highlighted2 + ' text.',
                       style='paragraph7')
grouped1 = StaticGroupedFlowables([paragraph6, paragraph7], style='grouped1')

doctree = DocumentTree([paragraph, paragraph2, paragraph3, paragraph4,
                        paragraph5, grouped1])

document = Document(doctree, ssheet2, EN)
container = FakeContainer(document)

def test_style():
    style = ssheet1['emphasized text']
    assert style.font_width == FontWidth.NORMAL
    assert style.font_slant == FontSlant.ITALIC
    assert style.font_size == Var('font-size')

    style = ssheet1['emphasized text 2']
    assert style.font_slant == FontSlant.OBLIQUE

    style = ssheet1['paragraph']
    assert style.space_above == 5*PT
    assert style.text_align == Var('text-align')
    assert style.font_width == FontWidth.NORMAL
    assert style.font_color == Var('font-color')
    assert style.indent_first == 2*PT

    style = ssheet2['paragraph']
    assert style.space_below == 10*PT
    assert style.indent_first == Var('indent-first')

    style = ssheet1['paragraph 2']
    assert style.padding_bottom == 3*PT

    style = ssheet2['paragraph 3']
    assert style.margin_left == 1*PT

    style = ssheet1['paragraph 4']
    assert style.base == 'paragraph'
    assert style.padding_top == 5*PT


def test_get_selector():
    assert ssheet2.get_selector('emphasized text') == emphasis_selector
    assert ssheet2.get_selector('emphasized text 2') == emphasis2_selector
    assert ssheet2.get_selector('paragraph') == paragraph_selector
    assert ssheet2.get_selector('paragraph 2') == paragraph2_selector
    assert ssheet2.get_selector('paragraph 3') == paragraph3_selector
    assert ssheet2.get_selector('paragraph 4') == paragraph4_selector
    assert ssheet2.get_selector('grouped 1') == grouped1_selector
    assert ssheet2.get_selector('paragraph 7') == paragraph7_selector
    assert ssheet2.get_selector('missing style') == missing_selector


def test_get_matches():
    assert ssheet2.get_value_for(emphasized, 'font_slant', document) == FontSlant.ITALIC
    assert ssheet2.get_value_for(paragraph5, 'font_slant', document) == FontSlant.UPRIGHT

    def helper(element):
        return [(match.style_name, match.stylesheet)
                for match in document.get_matches(element)]

    assert helper(emphasized) == [('emphasized text', 'ssheet1')]
    assert helper(emphasized2) == [('emphasized text 2', 'ssheet1')]
    assert helper(paragraph) == [('paragraph', 'ssheet2')]
    assert helper(paragraph2) == [('paragraph 2', 'ssheet1'),
                                  ('paragraph', 'ssheet2')]
    assert helper(paragraph3) == [('paragraph 3', 'ssheet2'),
                                  ('paragraph', 'ssheet2')]
    assert helper(paragraph4) == [('paragraph 4', 'ssheet2'),
                                  ('paragraph', 'ssheet2')]
    assert helper(paragraph5) == [('missing style', None),
                                  ('paragraph', 'ssheet2')]


def test_get_style():
    assert emphasized.get_style('font_weight', container) == FontWeight.MEDIUM
    assert emphasized.get_style('font_width', container) == FontWidth.CONDENSED
    assert emphasized.get_style('font_slant', container) == FontSlant.ITALIC

    assert emphasized2.get_style('font_weight', container) == FontWeight.MEDIUM
    assert emphasized2.get_style('font_width', container) == FontWidth.NORMAL
    assert emphasized2.get_style('font_slant', container) == FontSlant.OBLIQUE

    assert emphasized3.get_style('font_weight', container) == FontWeight.MEDIUM
    assert emphasized3.get_style('font_width', container) == FontWidth.NORMAL
    assert emphasized3.get_style('font_slant', container) == FontSlant.OBLIQUE

    assert highlighted2.get_style('font_color', container) == HexColor('00f')
    assert highlighted2.get_style('font_size', container) == 12*PT
    assert highlighted2.get_style('font_slant', container) == FontSlant.ITALIC

    assert paragraph.get_style('margin_left', container) == 0
    assert paragraph.get_style('margin_right', container) == 55*PT
    assert paragraph.get_style('space_above', container) == 5*PT
    assert paragraph.get_style('space_below', container) == 10*PT
    assert paragraph.get_style('font_weight', container) == FontWeight.MEDIUM
    assert paragraph.get_style('font_width', container) == FontWidth.CONDENSED
    assert paragraph.get_style('font_slant', container) == FontSlant.UPRIGHT
    assert paragraph.get_style('font_size', container) == 8*PT

    assert paragraph2.get_style('margin_left', container) == 0
    assert paragraph2.get_style('margin_right', container) == 0
    assert paragraph2.get_style('space_above', container) == 0
    assert paragraph2.get_style('space_below', container) == 0
    assert paragraph2.get_style('padding_top', container) == 0
    assert paragraph2.get_style('padding_bottom', container) == 3*PT
    assert paragraph2.get_style('font_weight', container) == FontWeight.MEDIUM
    assert paragraph2.get_style('font_width', container) == FontWidth.NORMAL
    assert paragraph2.get_style('font_slant', container) == FontSlant.UPRIGHT
    assert paragraph2.get_style('font_size', container) == 10*PT

    assert paragraph3.get_style('margin_left', container) == 1*PT
    assert paragraph3.get_style('margin_right', container) == 0
    assert paragraph3.get_style('space_above', container) == 0
    assert paragraph3.get_style('space_below', container) == 0
    assert paragraph3.get_style('padding_top', container) == 0
    assert paragraph3.get_style('padding_bottom', container) == 3*PT
    assert paragraph3.get_style('font_weight', container) == FontWeight.MEDIUM
    assert paragraph3.get_style('font_width', container) == FontWidth.NORMAL
    assert paragraph3.get_style('font_slant', container) == FontSlant.UPRIGHT
    assert paragraph3.get_style('font_size', container) == 10*PT

    # from 'paragraph' in ssheet1
    assert paragraph4.get_style('margin_right', container) == 55*PT
    assert paragraph4.get_style('space_above', container) == 5*PT
    assert paragraph4.get_style('font_size', container) == 8*PT
    # from 'paragraph' in ssheet2
    assert paragraph4.get_style('space_below', container) == 10*PT
    assert paragraph4.get_style('font_width', container) == FontWidth.CONDENSED
    # from 'paragraph 4' in sheet1
    assert paragraph4.get_style('padding_top', container) == 5*PT
    # from 'paragraph 4' in sheet2
    assert paragraph4.get_style('padding_right', container) == 2*PT

    assert paragraph5.get_style('font_slant', container) == FontSlant.UPRIGHT

    before_p4 = paragraph4.get_style('before', container)
    assert before_p4 == SingleStyledText('before p4', source=ssheet1)

    after_p4 = paragraph4.get_style('after', container)
    assert after_p4 == SingleStyledText('after p4', source=ssheet2)

    assert grouped1.get_style('padding_top', container) == 3*PT
    assert paragraph6.get_style('space_above', container) == 6*PT
    assert paragraph6.get_style('font_size', container) == 8*PT
    assert paragraph7.get_style('margin_left', container) == 7*PT
    assert paragraph7.get_style('padding_top', container) == 3*PT


def test_variable():
    assert emphasized.get_style('font_size', container) == 20*PT
    assert emphasized.get_style('font_color', container) == HexColor('f00')
    assert emphasized2.get_style('font_size', container) == 20*PT
    assert emphasized3.get_style('font_size', container) == 20*PT

    assert paragraph.get_style('text_align', container) == 'right'
    assert paragraph.get_style('font_color', container) == HexColor('f00')
    assert paragraph.get_style('indent_first', container) == 0.5*CM

    assert paragraph4.get_style('text_align', container) == 'right'
    assert paragraph4.get_style('font_color', container) == HexColor('f00')
    assert paragraph4.get_style('indent_first', container) == 0.5*CM
