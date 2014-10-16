
from rinoh import (
    StyleSheet, ClassSelector, ContextSelector,
    StyledText, MixedStyledText, FixedWidthSpace,
    Paragraph, Heading, ParagraphStyle, FixedSpacing, ProportionalSpacing,
    List, ListItem, DefinitionList, DefinitionTerm,
    GroupedFlowables, StaticGroupedFlowables,
    Header, Footer, Figure, Caption, Tabular, Framed, HorizontalRule,
    NoteMarkerBase, Note, TableOfContents, TableOfContentsEntry, Line, TabStop,
    DEFAULT, LEFT, RIGHT, CENTER, BOTH, MIDDLE,
    NUMBER, ROMAN_UC, CHARACTER_UC, SYMBOL,
    PT, INCH, CM, RED, BLUE, Color, Gray
)

from rinoh.font import TypeFamily
from rinoh.font.style import REGULAR, UPRIGHT, ITALIC, BOLD, SUPERSCRIPT

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

styles('error', ClassSelector(StyledText, 'error'),
       font_color=RED)

styles('hyperlink', ClassSelector(StyledText, 'link'),
       font_color=BLUE)

styles('literal', ClassSelector(Paragraph, 'literal'),
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

styles('block quote', ClassSelector(GroupedFlowables, 'block quote'),
       margin_left=1*CM)

styles('attribution', ClassSelector(Paragraph, 'attribution'),
       base='body',
       justify=RIGHT)

styles('line block', ContextSelector(ClassSelector(GroupedFlowables, 'line block'),
                                     ClassSelector(GroupedFlowables, 'line block')),
       margin_left=0.5*CM)

styles('title', ClassSelector(Paragraph, 'title'),
       typeface=ieee_family.serif,
       font_weight=REGULAR,
       font_size=18*PT,
       line_spacing=ProportionalSpacing(1.2),
       space_above=6*PT,
       space_below=6*PT,
       justify=CENTER)

styles('subtitle', ClassSelector(Paragraph, 'subtitle'),
       base='title',
       font_size=14*PT)

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
       number_format=ROMAN_UC,
       label_suffix='.' + FixedWidthSpace())

styles('unnumbered heading level 1', ClassSelector(Heading, 'unnumbered',
                                                   level=1),
       base='heading level 1',
       number_format=None)

styles('heading level 2', ClassSelector(Heading, level=2),
       base='heading level 1',
       font_slant=ITALIC,
       font_size=10*PT,
       small_caps=False,
       justify=LEFT,
       line_spacing=FixedSpacing(12*PT),
       space_above=6*PT,
       space_below=6*PT,
       number_format=CHARACTER_UC)

styles('heading level 3', ClassSelector(Heading, level=3),
       base='heading level 2',
       font_size=9*PT,
       font_slant=UPRIGHT,
       font_weight=BOLD,
       line_spacing=FixedSpacing(12*PT),
       space_above=3*PT,
       space_below=3*PT,
       number_format=None)

styles('heading level 4', ClassSelector(Heading, level=4),
       base='heading level 2',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=BOLD,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

styles('heading level 5', ClassSelector(Heading, level=5),
       base='heading level 2',
       font_size=9*PT,
       font_slant=ITALIC,
       font_weight=REGULAR,
       line_spacing=FixedSpacing(10*PT),
       space_above=2*PT,
       space_below=2*PT,
       number_format=None)

styles('topic', ClassSelector(GroupedFlowables, 'topic'),
       margin_left=0.5*CM)

styles('topic title', ContextSelector(ClassSelector(GroupedFlowables, 'topic'),
                                      ClassSelector(Paragraph, 'title')),
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

styles('rubric', ClassSelector(Paragraph, 'rubric'),
       base='topic title',
       justify=CENTER,
       font_color=Color(0.5, 0, 0))

styles('sidebar frame', ClassSelector(Framed, 'sidebar'),
       fill_color=Color(1.0, 1.0, 0.9))

styles('sidebar title', ContextSelector(ClassSelector(Framed, 'sidebar'),
                                        ClassSelector(GroupedFlowables),
                                        ClassSelector(Paragraph, 'title')),
       base='body',
       font_size=12*PT,
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

styles('sidebar subtitle', ContextSelector(ClassSelector(Framed, 'sidebar'),
                                           ClassSelector(GroupedFlowables),
                                           ClassSelector(Paragraph, 'subtitle')),
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=2*PT,
       space_below=2*PT)

styles('list item number', ContextSelector(ClassSelector(ListItem),
                                           ClassSelector(Paragraph)),
       base='body',
       indent_first=0,
       justify=RIGHT)

styles('enumerated list', ClassSelector(List, 'enumerated'),
       space_above=5*PT,
       space_below=5*PT,
       ordered=True,
       flowable_spacing=0*PT,
       number_format=NUMBER,
       label_suffix=')')

styles('nested enumerated list', ContextSelector(ClassSelector(ListItem),
                                                 ClassSelector(List,
                                                               'enumerated')),
       base='enumerated list',
       margin_left=10*PT)

styles('bulleted list', ClassSelector(List, 'bulleted'),
       base='enumerated list',
       ordered=False,
       label_suffix=None,
       flowable_spacing=0*PT)

styles('nested bulleted list', ContextSelector(ClassSelector(ListItem),
                                               ClassSelector(List, 'bulleted')),
       base='bulleted list',
       margin_left=10*PT)

styles('list item body', ContextSelector(ClassSelector(ListItem),
                                         ClassSelector(GroupedFlowables)),
       space_above=0,
       space_below=0,
       margin_left=0,
       margin_right=0)

styles('list item paragraph', ContextSelector(ClassSelector(ListItem),
                                              ClassSelector(GroupedFlowables),
                                              ClassSelector(Paragraph)),
       base='body',
       space_above=0*PT,
       space_below=0*PT,
       margin_left=0*PT,
       indent_first=0*PT)

styles('definition list', ClassSelector(DefinitionList),
       base='body')

styles('definition term', ClassSelector(DefinitionTerm),
       base='body',
       indent_first=0,
       font_weight=BOLD)

styles('definition term classifier', ClassSelector(StyledText, 'classifier'),
       font_weight=REGULAR)

styles('definition', ContextSelector(ClassSelector(DefinitionList),
                                     ClassSelector(GroupedFlowables)),
       margin_left=15*PT)


# field lists

styles('field name', ClassSelector(Paragraph, 'field_name'),
       base='body',
       indent_first=0,
       justify=LEFT,
       font_weight=BOLD)


# option lists

styles('option', ClassSelector(Paragraph, 'option_group'),
       base='body',
       indent_first=0,
       justify=LEFT)

styles('option string', ClassSelector(MixedStyledText, 'option_string'),
       base='body',
       typeface=ieee_family.mono,
       font_size=8*PT)

styles('option argument', ClassSelector(MixedStyledText, 'option_arg'),
       base='body',
       font_slant=ITALIC)


styles('admonition', ClassSelector(Framed, 'admonition'),
       space_above=5*PT,
       space_below=5*PT,
       padding_left=10*PT,
       padding_right=10*PT,
       padding_top=4*PT,
       padding_bottom=4*PT,
       fill_color=Color(0.94, 0.94, 1.0),
       stroke_width=1*PT,
       stroke_color=Gray(0.4))

styles('admonition title', ContextSelector(ClassSelector(Framed, 'admonition'),
                                           ClassSelector(GroupedFlowables),
                                           ClassSelector(Paragraph, 'title')),
       base='body',
       font_weight=BOLD,
       indent_first=0,
       space_above=5*PT,
       space_below=5*PT)

styles['red admonition title'] = ParagraphStyle(base='admonition title',
                                                font_color=RED)

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = ContextSelector(ClassSelector(Framed, 'admonition',
                                             admonition_type=admonition_type),
                               ClassSelector(GroupedFlowables),
                               ClassSelector(Paragraph, 'title'))
    styles.selectors[selector] = 'red admonition title'


styles('header', ClassSelector(Header),
       base='body',
       indent_first=0*PT,
       font_size=9*PT)

styles('footer', ClassSelector(Footer),
       base='header',
       indent_first=0*PT,
       justify=CENTER)

styles('footnote marker', ClassSelector(NoteMarkerBase, 'footnote'),
       position=SUPERSCRIPT,
       number_format=SYMBOL)

styles('citation marker', ClassSelector(NoteMarkerBase, 'citation'),
       label_prefix='[',
       label_suffix=']',
       custom_label=True)

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
       justify=BOTH,
       label_suffix='.' + FixedWidthSpace())

styles('figure legend',
       ContextSelector(ClassSelector(Figure),
                       ClassSelector(GroupedFlowables, 'legend')),
       margin_left=30*PT)

styles('figure legend paragraph',
       ContextSelector(ClassSelector(Figure),
                       ClassSelector(GroupedFlowables, 'legend'),
                       ClassSelector(Paragraph)),
       base='figure caption',
       space_above=5*PT,
       justify=LEFT)

styles('table of contents', ClassSelector(TableOfContents),
       base='body',
       indent_first=0,
       depth=3)

styles('toc level 1', ClassSelector(TableOfContentsEntry, depth=1),
       base='table of contents',
       font_weight=BOLD,
       tab_stops=[TabStop(0.6*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 2', ClassSelector(TableOfContentsEntry, depth=2),
       base='table of contents',
       margin_left=0.6*CM,
       tab_stops=[TabStop(1.2*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('toc level 3', ClassSelector(TableOfContentsEntry, depth=3),
       base='table of contents',
       margin_left=1.2*CM,
       tab_stops=[TabStop(1.8*CM),
                  TabStop(1.0, RIGHT, '. ')])

styles('L3 toc level 3', ContextSelector(ClassSelector(TableOfContents, level=2),
                                         ClassSelector(TableOfContentsEntry, depth=3)),
       base='table of contents',
       margin_left=0,
       tab_stops=[TabStop(0.6*CM),
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

styles('horizontal rule', ClassSelector(HorizontalRule),
       space_above=10*PT,
       space_below=15*PT,
       margin_left=40*PT,
       margin_right=40*PT)