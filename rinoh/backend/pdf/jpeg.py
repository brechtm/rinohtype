# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from io import SEEK_CUR
from struct import Struct


def create_reader(data_format, process_struct=lambda data: data[0]):
    data_struct = Struct('>' + data_format)
    def reader(jpeg_reader):
        data = data_struct.unpack(jpeg_reader._file.read(data_struct.size))
        return process_struct(data)
    return reader


class JPEGReader(object):
    def __init__(self, file_or_filename):
        print('opening', file_or_filename)
        try:
            self._file = open(file_or_filename, 'rb')
            self.filename = file_or_filename
        except TypeError:
            self._file = file_or_filename
            self.filename = None
        prefix, marker = self.read_uchar(), self.read_uchar()
        if (prefix, marker) != (0xFF, 0xD8):
            raise ValueError('Not a JPEG file')
        while True:
            prefix, marker = self.read_uchar(), self.read_uchar()
            while marker == 0xFF:
                marker = self.read_uchar()
            if prefix != 0xFF or marker == 0x00:
                raise ValueError('Invalid or corrupt JPEG file')
            print(hex(marker), 'at', hex(self._file.tell()), end=' ')
            if marker == 0xD9:
                print('end of image')
                data_after_eoi = self._file.read()
                if len(data_after_eoi):
                    print('data after EOI!')
                    print(data_after_eoi)
                break
            header_length = self.read_ushort()
            if (marker & 0xF0) == 0xC0 and marker not in (0xC4, 0xC8, 0xCC):
                self._parse_start_of_frame(header_length)
            elif marker == 0xE0:
                self._parse_jfif_segment(header_length)
            else:
                self._file.seek(header_length - 2, SEEK_CUR)
                if marker == 0xDA:
                    print('SOS (followed by compressed data)')
                    while True:
                        if self._file.read(1) == b'\xff':
                            byte = self.read_uchar()
                            if 0xD0 <= byte <= 0xD7:
                                print(hex(marker), 'at', hex(self._file.tell()),
                                      'restart marker')
                            elif byte != 0x00:  # escaped 0xFF
                                self._file.seek(-2, SEEK_CUR)
                                break
                else:
                    print('')

    read_uchar = create_reader('B')
    read_ushort = create_reader('H')

    SOF_HEADER = create_reader('B H H B', lambda tuple: tuple)

    def _parse_start_of_frame(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        (sample_precision, v_size, h_size, num_components) = self.SOF_HEADER()
        print('SOF', sample_precision, v_size, h_size, num_components)
        self._file.seek(resume_position)

    JFIF_HEADER = create_reader('5s 2s B H H B B', lambda tuple: tuple)

    def _parse_jfif_segment(self, header_length):
        (identifier, version, units,
         h_density, v_density, h_thumbnail, v_thumbnail) = self.JFIF_HEADER()
        assert identifier == b'JFIF\0'
        print('JFIF', version, units, h_density, v_density)
        thumbnail_size = 3 * h_thumbnail * v_thumbnail
        assert header_length == 16 + thumbnail_size
