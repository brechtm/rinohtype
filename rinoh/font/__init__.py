# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from warnings import warn

from .style import FontWeight, MEDIUM
from .style import FontSlant, UPRIGHT, OBLIQUE, ITALIC
from .style import FontWidth, NORMAL, CONDENSED, EXTENDED
from ..resource import Resource
from ..util import NotImplementedAttribute
from ..warnings import warn


# TODO: provide predefined Font objects for known font filenames?

class GlyphMetrics(object):
    __slots__ = ['name', 'width', 'bounding_box', 'code']

    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class Font(object):
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
        return self.slant != UPRIGHT

    # font metrics in font coordinates
    italic_angle = NotImplementedAttribute()
    ascender = NotImplementedAttribute()
    descender = NotImplementedAttribute()
    line_gap = NotImplementedAttribute()
    cap_height = NotImplementedAttribute()
    x_height = NotImplementedAttribute()
    stem_v = NotImplementedAttribute()

    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.filename = filename
        if not FontWeight.check_type(weight):
            raise ValueError('Unknown font weight. Must be one of {}'
                             .format(', '.join(FontWeight.values)))
        if not FontSlant.check_type(slant):
            raise ValueError('Unknown font slant. Must be one of {}'
                             .format(', '.join(FontSlant.values)))
        if not FontWidth.check_type(width):
            raise ValueError('Unknown font width. Must be one of {}'
                             .format(', '.join(FontWidth.values)))
        self.weight = weight
        self.slant = slant
        self.width = width
        # font metrics in Postscript points
        self.ascender_in_pt = self.ascender / self.units_per_em
        self.descender_in_pt = self.descender / self.units_per_em
        self.line_gap_in_pt = self.line_gap / self.units_per_em

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    def __hash__(self):
        return hash((self.name, self.filename))

    def get_glyph(self, char, variant):
        raise NotImplementedError

    def get_ligature(self, glyph, successor_glyph):
        raise NotImplementedError

    def get_kerning(self, a, b):
        raise NotImplementedError


class Typeface(Resource, dict):
    resource_type = 'typeface'

    def __new__(cls, name, *fonts, weight_order=FontWeight.values):
        if not fonts:
            return cls.from_string(name)
        else:
            return super().__new__(cls, name, *fonts, weight_order=weight_order)

    def __init__(self, name, *fonts, weight_order=FontWeight.values):
        self.name = name
        self.weight_order = weight_order
        for font in fonts:
            slants = self.setdefault(font.width, {})
            weights = slants.setdefault(font.slant, {})
            weights[font.weight] = font

    @classmethod
    def check_type(cls, value):
        return isinstance(value, cls)

    def get_font(self, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        def find_closest_style(style, styles, alternatives):
            try:
                return style, styles[style]
            except KeyError:
                for option in alternatives[style]:
                    try:
                        return option, styles[option]
                    except KeyError:
                        continue

        def find_closest_weight(weight, weights):
            index = FontWeight.values.index(weight)
            min_distance = len(FontWeight.values)
            closest = None
            for i, option in enumerate(FontWeight.values):
                if option in weights and abs(index - i) < min_distance:
                    min_distance = abs(index - i)
                    closest = option
            return closest, weights[closest]

        available_width, slants = find_closest_style(width, self,
                                                     FontWidth.alternatives)
        available_slant, weights = find_closest_style(slant, slants,
                                                      FontSlant.alternatives)
        available_weight, font = find_closest_weight(weight, weights)

        if (available_width != width or available_slant != slant or
            available_weight != weight):
            warn('{} has no {} {} {} style available. Falling back to {} {} {}'
                 .format(self.name, width, weight, slant,
                         available_width, available_weight, available_slant))
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
    """Descriptor that looks up the value from a given path in the instance (it
    is assumed the instance subclasses :class:`dict` which holds parsed data in
    a tree structure."""
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
