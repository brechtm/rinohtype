# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from io import SEEK_CUR
from struct import Struct

from .cos import Name, XObjectImage
from .filter import DCTDecode


__all__ = ['JPEGReader']


def create_reader(data_format, process_struct=lambda data: data[0]):
    data_struct = Struct('>' + data_format)
    def reader(jpeg_reader):
        data = data_struct.unpack(jpeg_reader._file.read(data_struct.size))
        return process_struct(data)
    return reader


class JPEGReader(XObjectImage):
    def __init__(self, file_or_filename):
        try:
            self._file = open(file_or_filename, 'rb')
            self.filename = file_or_filename
        except TypeError:
            self._file = file_or_filename
            self.filename = None
        width, height, bits_per_component, num_components = self._get_metadata()
        self.dpi = 144, 144                 # FIXME: read from JFIF or EXIF
        colorspace = Name('DeviceRGB')      # FIXME: determine from JPEG
        super().__init__(width, height, colorspace, bits_per_component,
                         filter=DCTDecode())
        self._file.seek(0)
        self._data.write(self._file.read())

    read_uchar = create_reader('B')

    read_ushort = create_reader('H')

    def _get_metadata(self):
        self._file.seek(0)
        prefix, marker = self.read_uchar(), self.read_uchar()
        if (prefix, marker) != (0xFF, 0xD8):
            raise ValueError('Not a JPEG file')
        while True:
            prefix, marker = self.read_uchar(), self.read_uchar()
            while marker == 0xFF:
                marker = self.read_uchar()
            if prefix != 0xFF or marker == 0x00:
                raise ValueError('Invalid or corrupt JPEG file')
            header_length = self.read_ushort()
            if marker == 0xE0:
                self._parse_jfif_segment(header_length)
            elif (marker & 0xF0) == 0xC0 and marker not in (0xC4, 0xC8, 0xCC):
                v_size, h_size, bits_per_component, num_components = \
                    self._parse_start_of_frame(header_length)
                break
            else:
                self._file.seek(header_length - 2, SEEK_CUR)
        return h_size, v_size, bits_per_component, num_components

    JFIF_HEADER = create_reader('5s 2s B H H B B', lambda tuple: tuple)

    def _parse_jfif_segment(self, header_length):
        (identifier, version, units,
         h_density, v_density, h_thumbnail, v_thumbnail) = self.JFIF_HEADER()
        assert identifier == b'JFIF\0'
        thumbnail_size = 3 * h_thumbnail * v_thumbnail
        assert header_length == 16 + thumbnail_size

    SOF_HEADER = create_reader('B H H B', lambda tuple: tuple)

    def _parse_start_of_frame(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        (sample_precision, v_size, h_size, num_components) = self.SOF_HEADER()
        self._file.seek(resume_position)
        return v_size, h_size, sample_precision, num_components
