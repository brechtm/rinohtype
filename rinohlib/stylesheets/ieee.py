
from rinoh import (
    StyleSheet, ClassSelector, ContextSelector,
    StyledText, Paragraph, Heading, FixedSpacing, ProportionalSpacing,
    List, ListItem, DefinitionList, GroupedFlowables, StaticGroupedFlowables,
    Header, Footer, Figure, Caption, Tabular, Framed,
    Note, TableOfContents, TableOfContentsEntry, Line, TabStop,
    DEFAULT, LEFT, RIGHT, CENTER, BOTH, NUMBER, ROMAN_UC, CHARACTER_UC, MIDDLE,
    PT, INCH, CM, RED, Color, Gray
)

from rinoh.font import TypeFamily
from rinoh.font.style import REGULAR, ITALIC, BOLD

from rinohlib.fonts.texgyre.termes import typeface as times
from rinohlib.fonts.texgyre.cursor import typeface as courier


ieee_family = TypeFamily(serif=times, mono=courier)

styles = StyleSheet('IEEE')

styles('body', ClassSelector(Paragraph),
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

styles('monospaced', ClassSelector(StyledText, 'monospaced'),
       font_size=9*PT,
       typeface=ieee_family.mono,
       hyphenate=False,
       ligatures=False)

styles('literal', ClassSelector(Paragraph, 'literal'),
       base='body',
       font_size=9*PT,
       justify=LEFT,
       indent_first=0,
       indent_left=1*CM,
       typeface=ieee_family.mono,
       ligatures=False)
       #noWrap=True,   # but warn on overflow
       #literal=True ?)

styles('block quote', ClassSelector(Paragraph, 'block quote'),
       base='body',
       indent_left=1*CM)

styles('title', ClassSelector(Paragraph, 'title'),
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=18*PT,
       line_spacing=ProportionalSpacing(1.2),
       space_above=6*PT,
       space_below=6*PT,
       justify=CENTER)

styles('author', ClassSelector(Paragraph, 'author'),
       base='title',
       font_size=12*PT,
       line_spacing=ProportionalSpacing(1.2))

styles('affiliation', ClassSelector(Paragraph, 'affiliation'),
       base='author',
       space_below=6*PT + 12*PT)

styles('heading level 1', ClassSelector(Heading, level=1),
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       small_caps=True,
       justify=CENTER,
       line_spacing=FixedSpacing(12*PT),
       space_above=18*PT,
       space_below=6*PT,
       numbering_style=ROMAN_UC)

styles('unnumbered heading level 1', ClassSelector(Heading, 'unnumbered',
                                                   level=1),
       base='heading level 1',
       numbering_style=None)

styles('heading level 2', ClassSelector(Heading, level=2),
       base='heading level 1',
       font_slant=ITALIC,
       font_size=10*PT,
       small_caps=False,
       justify=LEFT,
       line_spacing=FixedSpacing(12*PT),
       space_above=6*PT,
       space_below=6*PT,
       numbering_style=CHARACTER_UC)

styles('list item', ClassSelector(ListItem),
       label_width=12*PT,
       label_spacing=3*PT)

styles('list item number', ContextSelector(ClassSelector(ListItem),
                                           ClassSelector(Paragraph)),
       base='body',
       justify=RIGHT)

styles('enumerated list', ClassSelector(List, 'enumerated'),
       space_above=5*PT,
       space_below=5*PT,
       ordered=True,
       flowable_spacing=0*PT,
       numbering_style=NUMBER,
       numbering_separator=')')

styles('nested enumerated list', ContextSelector(ClassSelector(ListItem),
                                                 ClassSelector(List,
                                                               'enumerated')),
       base='enumerated list',
       indent_left=10*PT)

styles('bulleted list', ClassSelector(List, 'bulleted'),
       base='enumerated list',
       ordered=False,
       flowable_spacing=0*PT)

styles('nested bulleted list', ContextSelector(ClassSelector(ListItem),
                                               ClassSelector(List, 'bulleted')),
       base='bulleted list',
       indent_left=10*PT)

styles('list item paragraph', ContextSelector(ClassSelector(ListItem),
                                              ClassSelector(GroupedFlowables),
                                              ClassSelector(Paragraph)),
       base='body',
       space_above=0*PT,
       space_below=0*PT,
       indent_left=0*PT,
       indent_first=0*PT)

styles('definition list', ClassSelector(DefinitionList),
       base='body')

styles('definition', ContextSelector(ClassSelector(DefinitionList),
                                     ClassSelector(GroupedFlowables)),
       indent_left=15*PT)

styles('framed', ClassSelector(Framed),
       padding_left=10*PT,
       padding_right=10*PT,
       padding_top=4*PT,
       padding_bottom=4*PT,
       fill_color=Color(0.94, 0.94, 1.0),
       stroke_width=1*PT,
       stroke_color=Gray(0.4))

styles('header', ClassSelector(Header),
       base='body',
       indent_first=0*PT,
       font_size=9*PT)

styles('footer', ClassSelector(Footer),
       base='header',
       indent_first=0*PT,
       justify=CENTER)

styles('footnote paragraph', ContextSelector(ClassSelector(Note),
                                             ClassSelector(GroupedFlowables),
                                             ClassSelector(Paragraph)),
       base='body',
       font_size=9*PT,
       indent_first=0,
       line_spacing=FixedSpacing(10*PT))

styles('footnote label', ContextSelector(ClassSelector(Note),
                                         ClassSelector(Paragraph)),
       base='footnote paragraph',
       justify=RIGHT)

styles('figure', ClassSelector(Figure),
       space_above=10*PT,
       space_below=12*PT)

styles('figure caption', ContextSelector(ClassSelector(Figure),
                                         ClassSelector(Caption)),
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=9*PT,
       line_spacing=FixedSpacing(10*PT),
       indent_first=0*PT,
       space_above=20*PT,
       space_below=0*PT,
       justify=BOTH)

styles('table of contents', ClassSelector(TableOfContents),
       base='body',
       indent_first=0,
       depth=3)

styles('toc level 1', ClassSelector(TableOfContentsEntry, level=1),
       base='table of contents',
       font_weight=BOLD,
       tab_stops=[TabStop(0.6*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 2', ClassSelector(TableOfContentsEntry, level=2),
       base='table of contents',
       indent_left=0.6*CM,
       tab_stops=[TabStop(1.2*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 3', ClassSelector(TableOfContentsEntry, level=3),
       base='table of contents',
       indent_left=1.2*CM,
       tab_stops=[TabStop(1.8*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('tabular', ClassSelector(Tabular),
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       line_spacing=FixedSpacing(12*PT),
       indent_first=0*PT,
       space_above=0*PT,
       space_below=0*PT,
       justify=CENTER,
       vertical_align=MIDDLE,
       left_border='red line',
       right_border='red line',
       bottom_border='red line',
       top_border='red line')

styles('red line', ClassSelector(Line),
       stroke_width=0.2*PT,
       stroke_color=RED)

styles('thick line', ClassSelector(Line),
       stroke_width=1*PT)

styles('first row', ClassSelector(Tabular, 'NOMATCH'),  # TODO: find proper fix
       font_weight=BOLD,
       bottom_border='thick line')

styles('first column', ClassSelector(Tabular, 'NOMATCH'),
       font_slant=ITALIC,
       right_border='thick line')

styles('numbers', ClassSelector(Tabular, 'NOMATCH'),
       typeface=ieee_family.mono)

styles['tabular'].set_cell_style(styles['first row'], rows=0)
styles['tabular'].set_cell_style(styles['first column'], cols=0)
styles['tabular'].set_cell_style(styles['numbers'], rows=slice(1,None),
                                 cols=slice(1,None))
