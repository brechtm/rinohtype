# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Classes for fonts and typefaces.

"""

from warnings import warn

from .style import FontWeight, FontSlant, FontWidth
from ..resource import Resource, ResourceNotFound
from ..util import NotImplementedAttribute
from ..warnings import warn


__all__ = ['Font', 'Typeface']


# TODO: provide predefined Font objects for known font filenames?

class GlyphMetrics(object):
    """The metrics for an individual font glyph

    Args:
        name (str):
        width (float):
        bounding_box (4-tuple of floats):
        code (int):

    """

    __slots__ = ['name', 'width', 'bounding_box', 'code']

    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class Font(object):
    """A collection of glyphs in a particular style

    This is a base class for classes that parse different font formats. See
    :mod:`rinoh.font.type1` and :mod:`rinoh.font.opentype`.

    Args:
        filename (str): filename of the font file to load
        weight (FontWeight): weight of the font
        slant (FontSlant): slant of the font
        width (FontWidth): width of the font

    """

    units_per_em = NotImplementedAttribute()

    encoding = NotImplementedAttribute()
    """If no encoding is set for the :class:`Font`, glyphs are addressed by
    glyph ID (and thus support more than 256 glyphs)."""

    name = NotImplementedAttribute()
    bounding_box = NotImplementedAttribute()

    # font type
    fixed_pitch = NotImplementedAttribute()

    @property
    def italic(self):
        return self.slant != FontSlant.UPRIGHT

    # font metrics in font coordinates
    italic_angle = NotImplementedAttribute()
    ascender = NotImplementedAttribute()
    descender = NotImplementedAttribute()
    line_gap = NotImplementedAttribute()
    cap_height = NotImplementedAttribute()
    x_height = NotImplementedAttribute()
    stem_v = NotImplementedAttribute()

    def __init__(self, filename, weight, slant, width):
        self.filename = filename
        self.weight = FontWeight.validate(weight)
        self.slant = FontSlant.validate(slant)
        self.width = FontWidth.validate(width)
        # font metrics in Postscript points
        self.ascender_in_pt = self.ascender / self.units_per_em
        self.descender_in_pt = self.descender / self.units_per_em
        self.line_gap_in_pt = self.line_gap / self.units_per_em

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def __hash__(self):
        return hash((self.name, self.filename))

    def get_glyph(self, char, variant):
        """Return the glyph for a particular character

        If the glyph of requested font variant is not present in the font, the
        `normal` variant is returned instead. If that is not present either, an
        exception is raised.

        Args:
            char (str of length 1): the character for which to find the glyph
            variant (FontVariant): the variant of the glyph to return

        Returns:
            GlyphMetrics: the requested glyph

        Raises:
            MissingGlyphException: when the requested glyph is not present in
                the font

        """
        raise NotImplementedError

    def get_ligature(self, glyph, successor_glyph):
        """Return the ligature to replace the given glyphs

        If no ligature is defined in the font for the given glyphs, return
        ``None``.

        Args:
            glyph (GlyphMetrics): the first of the glyphs to combine
            successor_glyph (GlyphMetrics): the second of the glyphs to combine

        Returns:
            GlyphMetrics or None: the ligature to replace the given glyphs

        """
        raise NotImplementedError

    def get_kerning(self, a, b):
        """Look up the kerning for two glyphs

        Args:
            a (GlyphMetrics): the first of the glyphs
            b (GlyphMetrics): the second of the glyphs

        Returns:
            float: the kerning value in font units

        """
        raise NotImplementedError


class Typeface(Resource, dict):
    """A set of fonts that share common design features

    The fonts collected in a typeface differ in weight, width and/or slant.

    Args:
        *fonts (:class:`Font`): the fonts that make up this typeface

    """

    resource_type = 'typeface'

    def __new__(cls, name, *fonts):
        if not fonts:
            return cls.from_string(name)
        else:
            return super().__new__(cls, name, *fonts)

    def __init__(self, name, *fonts):
        self.name = name
        for font in fonts:
            slants = self.setdefault(font.width, {})
            weights = slants.setdefault(font.slant, {})
            weights[font.weight] = font

    def __str__(self):
        return self.name

    @classmethod
    def parse_string(cls, name, source):
        try:
            typeface = super().parse_string(name, source)
        except ResourceNotFound as rni:
            try:
                typeface = google_typeface(name)
            except GoogleFontNotFound:
                raise rni
        return typeface

    @classmethod
    def check_type(cls, value):
        return isinstance(value, cls)

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(value.name)

    @classmethod
    def doc_format(cls):
        return ('the name of a typeface. See :option:`rinoh --list-fonts` '
                'for a list of the available typefaces.')

    def fonts(self):
        """Generator yielding all fonts of this typeface

        Yields:
            Font: the next font in this typeface

        """
        for width in sorted(self):
            for slant in self[width]:
                for weight in sorted(self[width][slant]):
                    yield self[width][slant][weight]

    def get_font(self, weight=FontWeight.REGULAR, slant=FontSlant.UPRIGHT,
                 width=FontWidth.NORMAL):
        """Return the font matching or closest to the given style

        If a font with the given weight, slant and width is available, return
        it. Otherwise, return the font that is closest in style.

        Args:
            weight (FontWeight): weight of the font
            slant (FontSlant): slant of the font
            width (FontWidth): width of the font

        Returns:
            Font: the requested font

        """
        def find_closest(attribute, value, available):
            nearest = attribute.nearest(value, available)
            return nearest, available[nearest]

        available_width, slants = find_closest(FontWidth, width, self)
        available_slant, weights = find_closest(FontSlant, slant, slants)
        available_weight, font = find_closest(FontWeight, weight, weights)
        if ((available_width, available_slant, available_weight)
                != (width, slant, weight)):
            gv_width =  FontWidth.to_name(width)
            gv_weigth = FontWeight.to_name(weight)
            av_width = FontWidth.to_name(available_width)
            av_weight = FontWeight.to_name(available_weight)
            warn('{} does not include a {} {} {} font. Falling back to {} {} '
                 '{}'.format(self.name, gv_width, gv_weigth, slant, av_width,
                             av_weight, available_slant))
        return font

    # TODO: return bolder font than given font
    #def get_bolder(self, )

class TypeFamily(object):
    default = None

    def __init__(self, serif=None, sans=None, mono=None, cursive=None,
                 symbol=None, dingbats=None):
        self.serif = serif
        self.sans = sans
        self.mono = mono
        self.cursive = cursive
        self.symbol = symbol
        self.dingbats = dingbats


class LeafGetter(object):
    """Descriptor that looks up the value from a given path in the instance

    It is assumed the instance subclasses :class:`dict` which holds parsed data
    in a tree structure.

    Args:
        *path (str): the components of the path
        default: the default value to return if the given path is not present

    """
    def __init__(self, *path, default=None):
        self.path = path
        self.default = default

    def __get__(self, instance, owner):
        try:
            leaf = instance
            for item in self.path:
                leaf = leaf[item]
            return leaf
        except KeyError:
            if self.default:
                return self.default
            else:
                raise


class MissingGlyphException(Exception):
    """The font does not contain a glyph for the given unicode character"""


from .google import google_typeface, GoogleFontNotFound
