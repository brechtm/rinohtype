# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.



class GlyphMetrics(object):
    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class FontMetrics(dict):
    def get_glyph(self, char, variant=None):
        raise NotImplementedError

    def get_ligature(self, glyph, successor_glyph):
        raise NotImplementedError

    def get_kerning(self, a, b):
        raise NotImplementedError
