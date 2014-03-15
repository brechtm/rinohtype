

from rinoh import (
    StyleSheet, ClassSelector, ContextSelector,
    GroupedFlowables,
    StyledText, Paragraph, Heading,
    List, ListItem, DefinitionList,
    DEFAULT, LEFT, CENTER, RIGHT, BOTH, NUMBER,
    PT, CM
)

from rinoh.font import TypeFamily
from rinoh.font.style import REGULAR, ITALIC

from rinohlib.fonts.texgyre.pagella import typeface as pagella
from rinohlib.fonts.texgyre.cursor import typeface as cursor


fontFamily = TypeFamily(serif=pagella, mono=cursor)

styles = StyleSheet('Rinascimento')

styles('body', ClassSelector(Paragraph),
       typeface=fontFamily.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       line_spacing=DEFAULT,
       #indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=10*PT,
       justify=BOTH)

styles('title', ClassSelector(Paragraph, 'title'),
       typeface=fontFamily.serif,
       font_size=16*PT,
       line_spacing=DEFAULT,
       space_above=6*PT,
       space_below=6*PT,
       justify=CENTER)

styles('literal', ClassSelector(Paragraph, 'literal'),
       base='body',
       #font_size=9*PT,
       justify=LEFT,
       indent_left=1*CM,
       typeface=fontFamily.mono,
       ligatures=False)
       #noWrap=True,   # but warn on overflow
       #literal=True ?)

styles('block quote', ClassSelector(Paragraph, 'block quote'),
       base='body',
       indent_left=1*CM)

styles('heading level 1', ClassSelector(Heading, level=1),
       typeface=fontFamily.serif,
       font_size=14*PT,
       line_spacing=DEFAULT,
       space_above=14*PT,
       space_below=6*PT,
       numbering_style=None)

styles('heading level 2', ClassSelector(Heading, level=2),
       base='heading level 1',
       font_slant=ITALIC,
       font_size=12*PT,
       line_spacing=DEFAULT,
       space_above=6*PT,
       space_below=6*PT)

styles('monospaced', ClassSelector(StyledText, 'monospaced'),
       typeface=fontFamily.mono)

styles('list item', ClassSelector(ListItem),
       label_width=12*PT,
       label_spacing=3*PT)

styles('list item label', ContextSelector(ClassSelector(ListItem),
                                          ClassSelector(Paragraph)),
       base='body',
       justify=RIGHT)

styles('enumerated list', ClassSelector(List, 'enumerated'),
       base='body',
       ordered=True,
       indent_left=5*PT,
       flowable_spacing=0*PT,
       numbering_style=NUMBER,
       numbering_separator='.')

styles('bulleted list', ClassSelector(List, 'bulleted'),
       base='body',
       ordered=False,
       indent_left=5*PT,
       flowable_spacing=0*PT)

styles('list item paragraph', ContextSelector(ClassSelector(ListItem),
                                              ClassSelector(GroupedFlowables),
                                              ClassSelector(Paragraph)),
       base='body',
       indent_first=0)

styles('definition list', ClassSelector(DefinitionList),
       base='body')
