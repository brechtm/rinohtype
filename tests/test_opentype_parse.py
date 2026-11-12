# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import io
import struct

import pytest

from rinoh.font.opentype.parse import (array, context_array, create_reader,
                                       fixed, uint24, ushort)


class CountingBytesIO(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.read_count = 0

    def read(self, size=-1):
        self.read_count += 1
        return super().read(size)


def test_uint24_parses_big_endian_value():
    file = CountingBytesIO(bytes([0x12, 0x34, 0x56]))

    assert uint24(file) == 0x123456
    assert file.read_count == 1


def test_array_of_uint24_parses_each_item():
    file = CountingBytesIO(bytes([0x12, 0x34, 0x56, 0x65, 0x43, 0x21]))

    assert array(uint24, 2)(file) == [0x123456, 0x654321]
    assert file.read_count == 1


def test_scalar_processed_field_returns_processed_value():
    file = CountingBytesIO(struct.pack('>L', 1 << 16))

    assert fixed(file) == 1.0
    assert file.read_count == 1


def test_array_of_processed_fields_is_read_in_one_go():
    file = CountingBytesIO(struct.pack('>LLL', 1 << 16, 2 << 16, 3 << 16))

    assert array(fixed, 3)(file) == [1.0, 2.0, 3.0]
    assert file.read_count == 1


def test_array_of_multivalue_processed_fields_is_grouped_correctly():
    file = CountingBytesIO(struct.pack('>3B3B', 1, 2, 3, 4, 5, 6))
    three_bytes = create_reader('3B', lambda data: data)

    assert array(three_bytes, 2)(file) == [(1, 2, 3), (4, 5, 6)]
    assert file.read_count == 1


def test_reader_length_returns_an_array_reader():
    file = CountingBytesIO(struct.pack('>HHH', 1, 2, 3))

    assert ushort[3](file) == [1, 2, 3]
    assert file.read_count == 1


def test_context_array_reader_reads_count_from_the_table():
    file = CountingBytesIO(struct.pack('>HH', 1, 2))
    reader = ushort['Count']

    assert reader(file, table={'Count': 2}) == [1, 2]
    assert file.read_count == 1


def test_context_array_reader_multiplies_the_count():
    file = CountingBytesIO(struct.pack('>HH', 1, 2))
    reader = context_array(ushort, 'CountX2', multiplier=0.5)

    assert reader(file, table={'CountX2': 4}) == [1, 2]
    assert file.read_count == 1


def test_context_array_reader_parses_objects_in_sequence():
    def item_reader(file, table, **kwargs):
        return table['Offset'] + file.read(1)

    file = CountingBytesIO(b'abc')
    reader = context_array(item_reader, 'Count')

    assert reader(file, table={'Count': 3, 'Offset': b'-'}) == [b'-a',
                                                                 b'-b',
                                                                 b'-c']
    assert file.read_count == 3


def test_context_array_reader_passes_indirect_arguments():
    def item_reader(file, extra, table, **kwargs):
        return extra + table['Offset'] + file.read(1)

    file = CountingBytesIO(b'ab')
    reader = context_array(item_reader, 'Count', 'Extra')

    assert reader(file, table={'Count': 2, 'Extra': b'!',
                               'Offset': b'-'}) == [b'!-a', b'!-b']
    assert file.read_count == 2


def test_reader_length_is_the_size_of_a_value():
    assert len(ushort) == 2


def test_invalid_reader_length_raises():
    with pytest.raises(TypeError):
        ushort[1.5]
