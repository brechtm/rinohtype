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

class Font(object):
    units_per_em = None

    def __init__(self, metrics, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.metrics = metrics
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
        self.ascender = self.metrics.ascent / self.units_per_em
        self.descender = self.metrics.descent / self.units_per_em
        self.line_gap = self.metrics.line_gap / self.units_per_em

    @property
    def name(self):
        return self.metrics.name


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
