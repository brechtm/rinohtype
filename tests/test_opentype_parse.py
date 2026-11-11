# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import io
import struct

from rinoh.font.opentype.parse import array, create_reader, fixed


class CountingBytesIO(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.read_count = 0

    def read(self, size=-1):
        self.read_count += 1
        return super().read(size)


def test_array_of_processed_fields_is_read_in_one_go():
    file = CountingBytesIO(struct.pack('>LLL', 1 << 16, 2 << 16, 3 << 16))

    assert array(fixed, 3)(file) == [1.0, 2.0, 3.0]
    assert file.read_count == 1


def test_array_of_multivalue_processed_fields_is_grouped_correctly():
    file = CountingBytesIO(struct.pack('>3B3B', 1, 2, 3, 4, 5, 6))
    three_bytes = create_reader('3B', lambda data: data)

    assert array(three_bytes, 2)(file) == [(1, 2, 3), (4, 5, 6)]
    assert file.read_count == 1
