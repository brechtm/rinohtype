
from os import path

from rinoh.font import TypeFace
from rinoh.font.style import REGULAR, ITALIC, BOLD
from rinoh.font.opentype import OpenTypeFont


def filename(variant):
    return path.join(path.dirname(__file__),
                     'texgyrecursor-{}.otf'.format(variant))


regular = OpenTypeFont(filename('regular'), weight=REGULAR)
italic = OpenTypeFont(filename('italic'), weight=REGULAR, slant=ITALIC)
bold = OpenTypeFont(filename('bold'), weight=BOLD)
bold_italic = OpenTypeFont(filename('bolditalic'), weight=BOLD, slant=ITALIC)

typeface = TypeFace('TeXGyreCursor', regular, italic, bold, bold_italic)
