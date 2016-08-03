# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct

from .parse import OpenTypeTable, MultiFormatTable, short


class GlyfTable(OpenTypeTable):
    """Glyph outline table"""
    tag = 'glyf'

    def __init__(self, file, file_offset, loca_table):
        super().__init__(file, file_offset)
        self._file_offset = file_offset
        for index, glyph_offset in enumerate(loca_table.offsets()):
            if glyph_offset is not None:
                self[index] = GlyphHeader(file, file_offset + glyph_offset)
                # the glyph header is followed by the glyph description


class GlyphHeader(OpenTypeTable):
    entries = [('numberOfContours', short),
               ('xMin', short),
               ('yMin', short),
               ('xMax', short),
               ('yMax', short)]

    @property
    def bounding_box(self):
        return (self['xMin'], self['yMin'], self['xMax'], self['yMax'])


class LocaTable(OpenTypeTable):
    """Glyph location table"""
    tag = 'loca'

    def __init__(self, file, file_offset, version, num_glyphs):
        super().__init__(file, file_offset)
        self._num_glyphs = num_glyphs
        data_format = 'L' if version == 1 else 'H'
        data_struct = struct.Struct('>{}{}'.format(num_glyphs + 1, data_format))
        self._offsets = data_struct.unpack(file.read(data_struct.size))
        if version == 0:
            self._offsets = [offset * 2 for offset in self._offsets]

    def offsets(self):
        for index in range(self._num_glyphs):
            offset = self._offsets[index]
            if offset != self._offsets[index + 1]:
                yield offset
            else:
                yield None
