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
from rinoh.language import EN
from rinoh.paragraph import Paragraph
from rinoh.text import StyledText, SingleStyledText
from rinoh.style import StyleSheet, StyledMatcher, Specificity


emphasis_selector = StyledText.like('emphasis')
emphasis_2_selector = StyledText.like('emphasis2')
paragraph_selector = Paragraph
paragraph_2_selector = Paragraph.like('paragraph2')

matcher = StyledMatcher({
    'emphasized text': emphasis_selector,
    'emphasized text 2': emphasis_2_selector,
    'paragraph': paragraph_selector,
    'paragraph 2': paragraph_2_selector,
})

ssheet1 = StyleSheet('ssheet1', matcher)

ssheet1.variables['font-size'] = 5*PT
ssheet1.variables['text-align'] = 'center'
ssheet1.variables['font-color'] = HexColor('f00')

ssheet1('emphasized text',
        font_slant='italic',
        font_size=Var('font-size'))
ssheet1('emphasized text 2',
        font_slant='oblique')
ssheet1('paragraph',
        margin_right=55*PT,
        space_above=5*PT,
        text_align=Var('text-align'),
        font_color=Var('font-color'),
        indent_first=2*PT)
ssheet1('paragraph 2',
        padding_bottom=3*PT)



ssheet2 = StyleSheet('ssheet2', base=ssheet1)

ssheet2.variables['font-size'] = 20*PT
ssheet2.variables['text-align'] = 'right'
ssheet2.variables['indent-first'] = 0.5*CM

ssheet2('paragraph',
        space_below=10*PT,
        indent_first=Var('indent-first'))

emphasized = SingleStyledText('emphasized', style='emphasis')
emphasized2 = SingleStyledText('emphasized 2', style='emphasis2')
paragraph = Paragraph('A paragraph with ' + emphasized + ' text.')
paragraph2 = Paragraph('A second paragraph with ' + emphasized + ' text.',
                       style='paragraph2')

doctree = DocumentTree([paragraph])

document = Document(doctree, ssheet2, EN)
container = FakeContainer(document)

def test_style():
    style1 = ssheet1['emphasized text']
    assert style1.font_width == 'normal'
    assert style1.font_slant == 'italic'
    assert style1.font_size == Var('font-size')

    style2 = ssheet1['emphasized text 2']
    assert style2.font_slant == 'oblique'

    style3 = ssheet1['paragraph']
    assert style3.space_above == 5*PT
    assert style3.text_align == Var('text-align')
    assert style3.font_color == Var('font-color')
    assert style3.indent_first == 2*PT

    style4 = ssheet2['paragraph']
    assert style4.space_below == 10*PT
    assert style4.indent_first == Var('indent-first')

    style5 = ssheet2['paragraph 2']
    assert style5.padding_bottom == 3*PT


def test_get_selector():
    assert ssheet1.get_selector('emphasized text') == emphasis_selector
    assert ssheet1.get_selector('paragraph') == paragraph_selector


def test_get_styled():
    assert ssheet1.get_styled('emphasized text') == StyledText
    assert ssheet1.get_styled('paragraph') == Paragraph


def test_find_matches():
    match1, = ssheet1.find_matches(emphasized, None)
    assert match1.specificity == Specificity(0, 0, 1, 0, 1)
    assert match1.style_name == 'emphasized text'

    match2, = ssheet1.find_matches(paragraph, None)
    assert match2.specificity == Specificity(0, 0, 0, 0, 2)
    assert match2.style_name == 'paragraph'

    match3a, = ssheet2.find_matches(paragraph, None)
    assert match3a.specificity == Specificity(0, 0, 0, 0, 2)
    assert match3a.style_name == 'paragraph'


def test_find_style():
    assert ssheet1.find_style(emphasized, None) is ssheet1['emphasized text']
    assert ssheet1.find_style(paragraph, None) is ssheet1['paragraph']
    assert ssheet2.find_style(paragraph, None) is ssheet2['paragraph']


def test_get_style():
    assert emphasized.get_style('font_width', container) == 'normal'
    assert emphasized.get_style('font_slant', container) == 'italic'

    assert paragraph.get_style('margin_left', container) == 0
    assert paragraph.get_style('margin_right', container) == 55*PT
    assert paragraph.get_style('space_above', container) == 5*PT
    assert paragraph.get_style('space_below', container) == 10*PT


def test_variable():
    assert emphasized.get_style('font_size', container) == 20*PT

    assert paragraph.get_style('text_align', container) == 'right'
    assert paragraph.get_style('font_color', container) == HexColor('f00')
    assert paragraph.get_style('indent_first', container) == 0.5*CM
