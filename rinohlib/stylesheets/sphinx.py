from rinoh.color import Color, Gray, RED, GRAY90, GRAY50
from rinoh.dimension import PT, CM, PERCENT
from rinoh.number import NUMBER, SYMBOL, CHARACTER_UC
from rinoh.flowable import LEFT, RIGHT, CENTER
from rinoh.font import TypeFamily, Typeface
from rinoh.font.style import REGULAR, ITALIC, BOLD, SUPERSCRIPT
from rinoh.paragraph import (ParagraphStyle, TabStop, JUSTIFY,
                             FixedSpacing, ProportionalSpacing, SINGLE)
from rinoh.style import StyleSheet, Var
from rinoh.table import MIDDLE
from rinoh.text import FixedWidthSpace

from .matcher import matcher


palatino = Typeface('TeX Gyre Pagella')
courier = Typeface('TeX Gyre Cursor')
helvetica = Typeface('TeX Gyre Heros')


stylesheet = StyleSheet('Sphinx', matcher=matcher)

stylesheet.variables['fonts'] = TypeFamily(serif=palatino,
                                           sans=helvetica,
                                           mono=courier)

stylesheet['default'] = ParagraphStyle(typeface=Var('fonts').serif,
                                       font_weight=REGULAR,
                                       font_size=10*PT,
                                       line_spacing=FixedSpacing(12*PT),
                                       indent_first=0*PT,
                                       space_above=0*PT,
                                       space_below=0*PT,
                                       text_align=JUSTIFY,
                                       kerning=True,
                                       ligatures=True,
                                       hyphen_lang='en_US',
                                       hyphen_chars=4)

stylesheet('body',
           base='default',
           space_above=5*PT,
           space_below=0*PT,
           text_align=JUSTIFY)

stylesheet('italic',
       font_slant=ITALIC)

stylesheet('bold',
       font_weight=BOLD)

stylesheet('emphasis',
       font_slant=ITALIC)

stylesheet('strong',
       font_weight=BOLD)

stylesheet('quote',
       font_slant=ITALIC)

stylesheet('file path',
       typeface=Var('fonts').mono)

stylesheet('window title',
       font_weight=BOLD)

stylesheet('UI control',
       font_weight=BOLD)

stylesheet('menu cascade',
       font_weight=BOLD)

stylesheet('draft comment',
       font_color=RED)

stylesheet('title reference',
       font_slant=ITALIC)

stylesheet('monospaced',
           base='default',
           typeface=Var('fonts').mono,
           hyphenate=False,
           ligatures=False)

stylesheet('error',
       font_color=RED)

stylesheet('internal hyperlink',
           font_color=Color(0.208, 0.374, 0.486))

stylesheet('external hyperlink',
           font_color=Color(0.216, 0.439, 0.388))

stylesheet('broken hyperlink',
           font_color=GRAY50)

stylesheet('literal',
           base='default',
           typeface=Var('fonts').mono,
           text_align=LEFT,
           indent_first=0,
           space_above=4*PT,
           space_below=4*PT,
           ligatures=False,
           hyphenate=False)
           #noWrap=True,   # but warn on overflow
           #literal=True ?)

stylesheet('block quote',
       margin_left=1*CM)

stylesheet('attribution',
       base='default',
       text_align=RIGHT)

stylesheet('line block line',
       base='default',
       space_below=0*PT)

stylesheet('nested line block',
       margin_left=0.5*CM)

stylesheet('title',
       base='default',
       typeface=Var('fonts').serif,
       font_weight=REGULAR,
       font_size=18*PT,
       line_spacing=ProportionalSpacing(1.2),
       space_above=6*PT,
       space_below=6*PT,
       text_align=CENTER)

stylesheet('subtitle',
       base='title',
       font_size=14*PT)

stylesheet('date',
       base='title',
       font_size=10*PT,
       line_spacing=ProportionalSpacing(1.2))

stylesheet('author',
       base='title',
       font_size=12*PT,
       line_spacing=ProportionalSpacing(1.2))

stylesheet('affiliation',
       base='author',
       space_below=6*PT + 12*PT)

stylesheet('chapter',
       page_break=RIGHT)

stylesheet('heading level 1',
           typeface=Var('fonts').sans,
           font_weight=BOLD,
           font_size=16*PT,
           font_color=Color(0.126, 0.263, 0.361),
           line_spacing=SINGLE,
           space_above=18*PT,
           space_below=12*PT,
           number_format=NUMBER,
           label_suffix=FixedWidthSpace())

stylesheet('unnumbered heading level 1',
           base='heading level 1',
           number_format=None)

stylesheet('front matter section heading',
           base='unnumbered heading level 1')

stylesheet('heading level 2',
           base='heading level 1',
           font_size=14*PT,
           space_above=16*PT,
           space_below=10*PT)

stylesheet('heading level 3',
           base='heading level 2',
           font_size=12*PT,
           space_above=10*PT,
           space_below=6*PT)

stylesheet('heading level 4',
           base='heading level 3',
           font_size=9*PT,
           space_above=8*PT,
           space_below=4*PT,
           number_format=None)

stylesheet('heading level 5',
       base='heading level 2',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=REGULAR,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

stylesheet('other heading levels',
       base='heading level 5',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=REGULAR,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

stylesheet('appendix heading level 1',
           base='heading level 1',
           number_format=CHARACTER_UC)

stylesheet('topic',
       margin_left=0.5*CM)

stylesheet('topic title',
       base='default',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

stylesheet('post requirement')

stylesheet('rubric',
       base='topic title',
       text_align=CENTER,
       font_color=Color(0.5, 0, 0))

stylesheet('sidebar frame',
       space_above=5*PT,
       space_below=5*PT,
       padding_left=10*PT,
       padding_right=10*PT,
       padding_top=4*PT,
       padding_bottom=4*PT,
       fill_color=Color(1.0, 1.0, 0.9),
       stroke_width=1*PT,
       stroke_color=Gray(0.4))

stylesheet('sidebar title',
       base='default',
       font_size=12*PT,
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

stylesheet('sidebar subtitle',
       base='default',
       font_weight=BOLD,
       indent_first=0,
       space_above=2*PT,
       space_below=2*PT)

stylesheet('list item label',
       base='default',
       indent_first=0,
       text_align=RIGHT)

stylesheet('bulleted list item label',
       base='list item label')

stylesheet('enumerated list item label',
       base='list item label',
       label_suffix='.')

stylesheet('enumerated list',
           margin_left=8*PT,
           space_above=5*PT,
           space_below=5*PT,
           ordered=True,
           flowable_spacing=5*PT,
           number_format=NUMBER,
           label_suffix=')')

stylesheet('nested enumerated list',
           base='enumerated list',
           margin_left=10*PT)

stylesheet('bulleted list',
           base='enumerated list',
           ordered=False,
           label_suffix=None)

stylesheet('nested bulleted list',
       base='bulleted list',
       margin_left=10*PT)

stylesheet('steps list',
           base='enumerated list')

stylesheet('steps list item label',
           base='enumerated list item label')

stylesheet('choices list',
           base='bulleted list')

stylesheet('choices list item label',
           base='bulleted list item label')

stylesheet('list item body',
       space_above=0,
       space_below=0,
       margin_left=0,
       margin_right=0)

stylesheet('list item paragraph',
       base='default',
       space_above=0*PT,
       space_below=0*PT,
       margin_left=0*PT,
       indent_first=0*PT)

stylesheet('definition list')

stylesheet('definition term')

stylesheet('definition term paragraph',
           base='default',
           indent_first=0,
           font_weight=BOLD)

stylesheet('definition term classifier',
           font_weight=REGULAR)

stylesheet('definition',
           margin_left=20*PT)


# (Sphinx) version added/changed & deprecated

stylesheet('versionmodified', font_slant=ITALIC)

# (Sphinx) object descriptions

stylesheet('object description',
           space_above=6*PT,
           space_below=6*PT)

stylesheet('object signature',
           base='default')

stylesheet('object name', typeface=Var('fonts').mono, font_weight=BOLD)

stylesheet('additional name part', base='monospaced')

stylesheet('object type', )

stylesheet('object returns', )

stylesheet('object parentheses', font_size=11*PT)

stylesheet('object parameter list', )

stylesheet('object parameter (no emphasis)')

stylesheet('object parameter',
           base='object parameter (no emphasis)',
           font_slant=ITALIC)

stylesheet('object brackets', font_size=11*PT, font_weight=BOLD)

stylesheet('object optional parameter', )

stylesheet('object annotation', font_weight=BOLD)

stylesheet('object description content', base='definition')


# (Sphinx) production list

stylesheet('production list',
           space_above=5*PT,
           space_below=5*PT)

stylesheet('production')

stylesheet('token name',
           base='literal',
           font_weight=BOLD,
           space_above=0,
           space_below=0)

stylesheet('token definition',
           base='literal',
           space_above=0,
           space_below=0)


# field lists

stylesheet('field name',
       base='default',
       indent_first=0,
       text_align=LEFT,
       font_weight=BOLD)


# option lists

stylesheet('option',
       base='default',
       indent_first=0,
       text_align=LEFT)

stylesheet('option string',
       base='default',
       typeface=Var('fonts').mono,
       font_size=8*PT)

stylesheet('option argument',
       base='default',
       font_slant=ITALIC)


stylesheet('admonition',
       space_above=5*PT,
       space_below=5*PT,
       padding_left=10*PT,
       padding_right=10*PT,
       padding_top=4*PT,
       padding_bottom=4*PT,
       fill_color=Color(0.94, 0.94, 1.0),
       stroke_width=1*PT,
       stroke_color=Gray(0.4))

stylesheet('admonition title',
       base='default',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    stylesheet(admonition_type + ' admonition title',
           base='admonition title',
           font_color=RED)

stylesheet('header',
           base='default',
           typeface=Var('fonts').sans,
           font_size=10*PT,
           font_weight=BOLD,
           indent_first=0*PT,
           tab_stops=[TabStop(50*PERCENT, CENTER),
                      TabStop(100*PERCENT, RIGHT)])


stylesheet('line under header',
           space_above=2*PT,
           stroke_width=0.2*PT)

stylesheet('footer',
           base='header')

stylesheet('line above footer',
           stroke_width=0.2*PT)

stylesheet('footnote marker',
       position=SUPERSCRIPT,
       number_format=SYMBOL)

stylesheet('citation marker',
       label_prefix='[',
       label_suffix=']',
       custom_label=True)

stylesheet('footnote paragraph',
       base='default',
       font_size=9*PT,
       indent_first=0,
       line_spacing=FixedSpacing(10*PT))

stylesheet('footnote label',
       base='footnote paragraph',
       text_align=RIGHT)

stylesheet('figure',
       space_above=10*PT,
       space_below=12*PT)


stylesheet('image',
           space_above=10*PT,
           horizontal_align=CENTER)

stylesheet('caption',
           base='default',
           typeface=Var('fonts').serif,
           font_size=9*PT,
           line_spacing=FixedSpacing(10*PT),
           indent_first=0*PT,
           space_above=4*PT,
           space_below=0*PT,
           text_align=CENTER,
           label_suffix='.' + FixedWidthSpace())

stylesheet('figure legend',
       margin_left=30*PT)

stylesheet('figure legend paragraph',
       base='caption',
       space_above=5*PT,
       text_align=LEFT)

stylesheet('table of contents section',
           show_in_toc=False)

stylesheet('table of contents',
           base='default',
           indent_first=0,
           depth=2)

stylesheet('toc level 1',
           base='table of contents',
           font_weight=BOLD,
           space_above=14*PT,
           tab_stops=[TabStop(0.6*CM),
                      TabStop(100*PERCENT, RIGHT)])

stylesheet('toc level 2',
           base='table of contents',
           margin_left=0.6*CM,
           tab_stops=[TabStop(1.0*CM),
                      TabStop(100*PERCENT, RIGHT, fill='.  ')])

stylesheet('toc level 3',
           base='table of contents',
           margin_left=1.6*CM,
           tab_stops=[TabStop(1.4*CM),
                      TabStop(100*PERCENT, RIGHT, fill='.  ')])

stylesheet('L3 toc level 3',
           base='table of contents',
           margin_left=0,
           tab_stops=[TabStop(0.6*CM),
                      TabStop(100*PERCENT, RIGHT, '. ')])

stylesheet('table',
       space_above=5*PT,
       space_below=5*PT,
       horizontal_align=CENTER)

stylesheet('table cell',
       space_above=2*PT,
       space_below=2*PT,
       margin_left=2*PT,
       margin_right=2*PT,
       vertical_align=MIDDLE)

stylesheet('table body cell background on even row',
       fill_color=GRAY90)

stylesheet('table body cell paragraph',
       base='default',
       font_size=9*PT,
       indent_first=0)

stylesheet('table body cell list item number',
       base='table body cell paragraph',
       indent_first=0,
       text_align=RIGHT)

stylesheet('table head cell paragraph',
       base='table body cell paragraph',
       font_weight=BOLD,
       text_align=CENTER)

stylesheet('table first column paragraph',
           base='table body cell paragraph',
           text_align=LEFT)

stylesheet('table top border',
       stroke_width=1*PT,
       stroke_color=Gray(0))

stylesheet('table bottom border',
       base='table top border')

stylesheet('table head bottom border',
       base='table top border',
       stroke_width=0.5*PT)

stylesheet('table body top border',
       base='table head bottom border')

stylesheet('horizontal rule',
       space_above=10*PT,
       space_below=15*PT,
       margin_left=40*PT,
       margin_right=40*PT)


# title page

stylesheet('title page title',
           typeface=Var('fonts').sans,
           font_size=26*PT,
           text_align=CENTER)

stylesheet('title page subtitle',
           base='title page title',
           font_size=20*PT,
           space_above=10*PT)

stylesheet('title page author',
           typeface=Var('fonts').sans,
           font_size=18*PT,
           text_align=CENTER,
           space_above=80*PT)

stylesheet('title page date',
           typeface=Var('fonts').sans,
           font_size=14*PT,
           text_align=CENTER,
           space_above=20*PT)

# index

stylesheet('level 1 index entry',
           base='default')

stylesheet('level 2 index entry',
           base='level 1 index entry',
           indent_first=20*PT)

stylesheet('level 3 index entry',
           base='level 1 index entry',
           indent_first=40*PT)

stylesheet('level 4 index entry',
           base='level 1 index entry',
           indent_first=60*PT)
