
from rinoh import (StyleSheet, ClassSelector, ContextSelector,
                   PT, CM, INCH, LEFT, RIGHT, CENTER, BOTH,
                   TOP, BOTTOM, MIDDLE,
                   FixedWidthSpace, TabStop,
                   FixedSpacing, ProportionalSpacing,
                   ROMAN_UC, CHARACTER_UC, NUMBER, SYMBOL,
                   Color, Gray, RED, BLUE, GRAY90)
from rinoh.font import TypeFamily
from rinoh.font.style import REGULAR, UPRIGHT, ITALIC, BOLD, SUPERSCRIPT

from rinohlib.fonts.texgyre.termes import typeface as times
from rinohlib.fonts.texgyre.cursor import typeface as courier

from .matcher import matcher

ieee_family = TypeFamily(serif=times, mono=courier)

styles = StyleSheet('IEEE', matcher=matcher)

styles('body',
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       line_spacing=FixedSpacing(12*PT),
       indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=0*PT,
       justify=BOTH,
       kerning=True,
       ligatures=True,
       hyphen_lang='en_US',
       hyphen_chars=4)

styles('monospaced',
       font_size=9*PT,
       typeface=ieee_family.mono,
       hyphenate=False,
       ligatures=False)

styles('error',
       font_color=RED)

styles('hyperlink',
       font_color=BLUE)

styles('literal',
       base='body',
       font_size=9*PT,
       justify=LEFT,
       indent_first=0,
       margin_left=0.5*CM,
       typeface=ieee_family.mono,
       ligatures=False,
       hyphenate=False)
       #noWrap=True,   # but warn on overflow
       #literal=True ?)

styles('block quote',
       margin_left=1*CM)

styles('attribution',
       base='body',
       justify=RIGHT)

styles('nested line block',
       margin_left=0.5*CM)

styles('title',
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=18*PT,
       line_spacing=ProportionalSpacing(1.2),
       space_above=6*PT,
       space_below=6*PT,
       justify=CENTER)

styles('subtitle',
       base='title',
       font_size=14*PT)

styles('author',
       base='title',
       font_size=12*PT,
       line_spacing=ProportionalSpacing(1.2))

styles('affiliation',
       base='author',
       space_below=6*PT + 12*PT)

styles('heading level 1',
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       small_caps=True,
       justify=CENTER,
       line_spacing=FixedSpacing(12*PT),
       space_above=18*PT,
       space_below=6*PT,
       number_format=ROMAN_UC,
       label_suffix='.' + FixedWidthSpace())

styles('unnumbered heading level 1',
       base='heading level 1',
       number_format=None)

styles('heading level 2',
       base='heading level 1',
       font_slant=ITALIC,
       font_size=10*PT,
       small_caps=False,
       justify=LEFT,
       line_spacing=FixedSpacing(12*PT),
       space_above=6*PT,
       space_below=6*PT,
       number_format=CHARACTER_UC)

styles('heading level 3',
       base='heading level 2',
       font_size=9*PT,
       font_slant=UPRIGHT,
       font_weight=BOLD,
       line_spacing=FixedSpacing(12*PT),
       space_above=3*PT,
       space_below=3*PT,
       number_format=None)

styles('heading level 4',
       base='heading level 2',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=BOLD,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

styles('heading level 5',
       base='heading level 2',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=REGULAR,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

styles('topic',
       margin_left=0.5*CM)

styles('topic title',
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

styles('rubric',
       base='topic title',
       justify=CENTER,
       font_color=Color(0.5, 0, 0))

styles('sidebar frame',
       fill_color=Color(1.0, 1.0, 0.9))

styles('sidebar title',
       base='body',
       font_size=12*PT,
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

styles('sidebar subtitle',
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=2*PT,
       space_below=2*PT)

styles('list item number',
       base='body',
       indent_first=0,
       justify=RIGHT)

styles('enumerated list',
       space_above=5*PT,
       space_below=5*PT,
       ordered=True,
       flowable_spacing=0*PT,
       number_format=NUMBER,
       label_suffix=')')

styles('nested enumerated list',
       base='enumerated list',
       margin_left=10*PT)

styles('bulleted list',
       base='enumerated list',
       ordered=False,
       label_suffix=None,
       flowable_spacing=0*PT)

styles('nested bulleted list',
       base='bulleted list',
       margin_left=10*PT)

styles('list item body',
       space_above=0,
       space_below=0,
       margin_left=0,
       margin_right=0)

styles('list item paragraph',
       base='body',
       space_above=0*PT,
       space_below=0*PT,
       margin_left=0*PT,
       indent_first=0*PT)

styles('definition list',
       base='body')

styles('definition term',
       base='body',
       indent_first=0,
       font_weight=BOLD)

styles('definition term classifier',
       font_weight=REGULAR)

styles('definition',
       margin_left=15*PT)


# field lists

styles('field name',
       base='body',
       indent_first=0,
       justify=LEFT,
       font_weight=BOLD)


# option lists

styles('option',
       base='body',
       indent_first=0,
       justify=LEFT)

styles('option string',
       base='body',
       typeface=ieee_family.mono,
       font_size=8*PT)

styles('option argument',
       base='body',
       font_slant=ITALIC)


styles('admonition',
       space_above=5*PT,
       space_below=5*PT,
       padding_left=10*PT,
       padding_right=10*PT,
       padding_top=4*PT,
       padding_bottom=4*PT,
       fill_color=Color(0.94, 0.94, 1.0),
       stroke_width=1*PT,
       stroke_color=Gray(0.4))

styles('admonition title',
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    styles(admonition_type + ' admonition title',
           base='admonition title',
           font_color=RED)

styles('header',
       base='body',
       indent_first=0*PT,
       font_size=9*PT)

styles('footer',
       base='header',
       indent_first=0*PT,
       justify=CENTER)

styles('footnote marker',
       position=SUPERSCRIPT,
       number_format=SYMBOL)

styles('citation marker',
       label_prefix='[',
       label_suffix=']',
       custom_label=True)

styles('footnote paragraph',
       base='body',
       font_size=9*PT,
       indent_first=0,
       line_spacing=FixedSpacing(10*PT))

styles('footnote label',
       base='footnote paragraph',
       justify=RIGHT)

styles('figure',
       space_above=10*PT,
       space_below=12*PT)


styles('image',
       horizontal_align=CENTER)

styles('figure caption',
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=9*PT,
       line_spacing=FixedSpacing(10*PT),
       indent_first=0*PT,
       space_above=4*PT,
       space_below=0*PT,
       justify=BOTH,
       label_suffix='.' + FixedWidthSpace())

styles('figure legend',
       margin_left=30*PT)

styles('figure legend paragraph',
       base='figure caption',
       space_above=5*PT,
       justify=LEFT)

styles('table of contents',
       base='body',
       indent_first=0,
       depth=3)

styles('toc level 1',
       base='table of contents',
       font_weight=BOLD,
       tab_stops=[TabStop(0.6*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 2',
       base='table of contents',
       margin_left=0.6*CM,
       tab_stops=[TabStop(1.2*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 3',
       base='table of contents',
       margin_left=1.2*CM,
       tab_stops=[TabStop(1.8*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('L3 toc level 3',
       base='table of contents',
       margin_left=0,
       tab_stops=[TabStop(0.6*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('table',
       space_above=5*PT,
       space_below=5*PT,
       horizontal_align=CENTER)

styles('table cell',
       space_above=2*PT,
       space_below=2*PT,
       margin_left=2*PT,
       margin_right=2*PT,
       vertical_align=MIDDLE)

styles('table body cell background on even row',
       fill_color=GRAY90)

styles('table body cell paragraph',
       base='body',
       font_size=9*PT,
       indent_first=0)

styles('table body cell list item number',
       base='table body cell paragraph',
       indent_first=0,
       justify=RIGHT)

styles('table head cell paragraph',
       base='table body cell paragraph',
       font_weight=BOLD,
       justify=CENTER)

styles('table top border',
       stroke_width=1*PT,
       stroke_color=Gray(0))

styles('table bottom border',
       base='table top border')

styles('table head inner border',
       base='table top border',
       stroke_width=0.5*PT)

styles('table body top border',
       base='table head inner border')

styles('horizontal rule',
       space_above=10*PT,
       space_below=15*PT,
       margin_left=40*PT,
       margin_right=40*PT)
