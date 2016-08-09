# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .parse import OpenTypeTable, ushort, fword, array, Packed


class KerningCoverage(Packed):
    reader = ushort
    fields = [('horizontal', 0x01, bool),
              ('minimum', 0x02, bool),
              ('cross-stream', 0x04, bool),
              ('override', 0x08, bool),
              ('format', 0xF0, int),]


class KernSubTable(OpenTypeTable):
    """Kerning subtable"""
    entries = [('version', ushort),
               ('length', ushort),
               ('coverage', KerningCoverage)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        if self['coverage']['format'] == 0:
            self.pairs = {}
            (n_pairs, search_range,
             entry_selector, range_shift) = array(ushort, 4)(file)
            for i in range(n_pairs):
                left, right, value = ushort(file), ushort(file), fword(file)
                left_dict = self.pairs.setdefault(left, {})
                left_dict[right] = value
        else:
            raise NotImplementedError


class KernTable(OpenTypeTable):
    """Kerning table (only for TrueType outlines)"""
    tag = 'kern'
    entries = [('version', ushort),
               ('nTables', ushort)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        for i in range(self['nTables']):
            subtable = KernSubTable(file, file.tell())
            self[subtable['coverage']['format']] = subtable
