
from rinoh.dimension import PT, CM
from rinoh.font.style import REGULAR, SUPERSCRIPT
from rinoh.number import NUMBER
from rinoh.paragraph import LEFT, CENTER
from rinoh.text import FixedWidthSpace
from rinoh.style import StyleSheet, Var

from rinohlib.stylesheets.ieee import styles as IEEE_STYLESHEET


stylesheet = StyleSheet('SomeStyle', base=IEEE_STYLESHEET)

stylesheet('body',
           base=stylesheet.base['body'],
           indent_first=0,
           space_below=6*PT)

stylesheet('heading level 1',
           typeface=Var('ieee_family').sans,
           font_size=14*PT,
           space_above=18*PT,
           space_below=6*PT,
           label_suffix='.' + FixedWidthSpace())

stylesheet('heading level 2',
           base='heading level 1',
           font_size=12*PT,
           space_above=6*PT,
           space_below=6*PT,
           label_suffix='.' + FixedWidthSpace())

stylesheet('figure caption',
           typeface=Var('ieee_family').sans,
           font_weight=REGULAR,
           font_size=9*PT,
           space_above=4*PT,
           space_below=0*PT,
           justify=CENTER,
           label_suffix='.' + FixedWidthSpace())

stylesheet('footnote marker',
           position=SUPERSCRIPT,
           number_format=NUMBER)

stylesheet('title page title',
           typeface=Var('ieee_family').sans,
           font_size=26*PT,
           justify=CENTER,
           space_below=80*PT)

stylesheet('title page author',
           typeface=Var('ieee_family').sans,
           font_size=18*PT,
           justify=CENTER)

stylesheet('title page extra',
           typeface=Var('ieee_family').sans,
           font_size=18*PT,
           justify=CENTER,
           space_above=10*CM)

stylesheet('table body cell paragraph',
           base='default',
           font_size=9*PT,
           indent_first=0,
           justify=CENTER)

stylesheet('table first column paragraph',
           base='table body cell paragraph',
           justify=LEFT)
