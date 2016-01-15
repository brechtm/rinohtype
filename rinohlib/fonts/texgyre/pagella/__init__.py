
from os import path

from rinoh.font import Typeface
from rinoh.font.style import REGULAR, ITALIC, BOLD
from rinoh.font.opentype import OpenTypeFont


def filename(variant):
    return path.join(path.dirname(__file__),
                     'texgyrepagella-{}.otf'.format(variant))


regular = OpenTypeFont(filename('regular'), weight=REGULAR)
italic = OpenTypeFont(filename('italic'), weight=REGULAR, slant=ITALIC)
bold = OpenTypeFont(filename('bold'), weight=BOLD)
bold_italic = OpenTypeFont(filename('bolditalic'), weight=BOLD, slant=ITALIC)

typeface = Typeface('TeXGyrePagella', regular, italic, bold, bold_italic)
