# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
from warnings import warn

from .style import WEIGHTS, MEDIUM
from .style import SLANTS, UPRIGHT, OBLIQUE, ITALIC
from .style import WIDTHS, NORMAL, CONDENSED, EXTENDED
from ..warnings import RinohWarning


# TODO: provide predefined Font objects for known font filenames?

class GlyphMetrics(object):
    __slots__ = ['name', 'width', 'bounding_box', 'code']

    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class NotImplementedAttribute(object):
    """Descriptor raising :class:`NotImplementedError` on attribute access"""
    def __get__(self, instance, owner):
        raise NotImplementedError('Attribute implementation is missing in '
                                  'subclass')


class Font(object):
    units_per_em = NotImplementedAttribute()

    encoding = NotImplementedAttribute()
    """If no encoding is set for the :class:`Font`, glyphs are addressed by
    glyph ID (and thus support more than 256 glyphs)."""

    name = NotImplementedAttribute()
    bounding_box = NotImplementedAttribute()

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
        if weight not in WEIGHTS:
            raise ValueError('Unknown font weight. Must be one of {}'
                             .format(', '.join(WEIGHTS)))
        if slant not in SLANTS:
            raise ValueError('Unknown font slant. Must be one of {}'
                             .format(', '.join(SLANTS)))
        if width not in WIDTHS:
            raise ValueError('Unknown font width. Must be one of {}'
                             .format(', '.join(WIDTHS)))
        self.weight = weight
        self.slant = slant
        self.width = width
        # font metrics in Postscript points
        self.ascender_in_pt = self.ascender / self.units_per_em
        self.descender_in_pt = self.descender / self.units_per_em
        self.line_gap_in_pt = self.line_gap / self.units_per_em

    def __hash__(self):
        return hash((self.name, self.filename))

    def get_glyph(self, char, variant=None):
        raise NotImplementedError

    def get_ligature(self, glyph, successor_glyph):
        raise NotImplementedError

    def get_kerning(self, a, b):
        raise NotImplementedError


class TypeFace(dict):
    def __init__(self, name, *fonts, weight_order=WEIGHTS):
        self.name = name
        self.weight_order = weight_order
        for font in fonts:
            slants = self.setdefault(font.width, {})
            weights = slants.setdefault(font.slant, {})
            weights[font.weight] = font

    width_alternatives = {NORMAL: (CONDENSED, EXTENDED),
                          CONDENSED: (NORMAL, EXTENDED),
                          EXTENDED: (NORMAL, CONDENSED)}

    slant_alternatives = {UPRIGHT: (OBLIQUE, ITALIC),
                          OBLIQUE: (ITALIC, UPRIGHT),
                          ITALIC: (OBLIQUE, UPRIGHT)}

    def get(self, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
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
            index = WEIGHTS.index(weight)
            min_distance = len(WEIGHTS)
            closest = None
            for i, option in enumerate(WEIGHTS):
                if option in weights and abs(index - i) < min_distance:
                    min_distance = abs(index - i)
                    closest = option
            return closest, weights[closest]

        available_width, slants = find_closest_style(width, self,
                                                     self.width_alternatives)
        available_slant, weights = find_closest_style(slant, slants,
                                                      self.slant_alternatives)
        available_weight, font = find_closest_weight(weight, weights)

        if (available_width != width or available_slant != slant or
            available_weight != weight):
            warn('{} has no {} {} {} style available. Falling back to {} {} {}'
                 .format(self.name, width, weight, slant,
                         available_width, available_weight, available_slant),
                 RinohWarning)

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
