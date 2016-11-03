# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from ..attribute import OptionSet


__all__ = ['FontWeight', 'FontSlant', 'FontWidth', 'FontVariant',
           'TextPosition']


class FontWeight(OptionSet):
    values = ('hairline', 'thin', 'ultra-light', 'extra-light', 'light',
              'book', 'regular', 'medium', 'demi-bold', 'bold', 'extra-bold',
              'heavy', 'black', 'extra-black', 'ultra-black')


class FontSlant(OptionSet):
    values = 'upright', 'oblique', 'italic'
    alternatives = dict(upright=('oblique', 'italic'),
                        oblique=('italic', 'upright'),
                        italic=('oblique', 'upright'))


class FontWidth(OptionSet):
    values = 'normal', 'condensed', 'extended'
    alternatives = dict(normal=('condensed', 'extended'),
                        condensed=('normal', 'extended'),
                        extended=('normal', 'condensed'))


class FontVariant(OptionSet):
    values = 'normal', 'small capital', 'oldstyle figures'


class TextPosition(OptionSet):
    values = 'normal', 'superscript', 'subscript'


# for backward compatibility
for option_set in (FontWeight, FontSlant, FontWidth):
    for value in option_set.values:
        globals()[value.replace('-', '_').upper()] = value
