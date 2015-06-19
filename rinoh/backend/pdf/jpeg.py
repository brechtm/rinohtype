# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from io import SEEK_CUR
from struct import Struct, unpack, calcsize

from .cos import Name, XObjectImage
from .filter import DCTDecode


__all__ = ['JPEGReader']


DPCM = 'dpcm'
DPI = 'dpi'


def create_reader(data_format, process_struct=lambda data: data[0], endian='>'):
    data_struct = Struct(endian + data_format)
    def reader(jpeg_reader):
        data = data_struct.unpack(jpeg_reader._file.read(data_struct.size))
        return process_struct(data)
    return reader


class JPEGReader(XObjectImage):
    COLOR_SPACE = {1: 'DeviceGray',
                   3: 'DeviceRGB',
                   4: 'DeviceCMYK'}

    def __init__(self, file_or_filename):
        try:
            self._file = open(file_or_filename, 'rb')
            self.filename = file_or_filename
        except TypeError:
            self._file = file_or_filename
            self.filename = None
        self.dpi = 72, 72
        width, height, bits_per_component, num_components = self._get_metadata()
        if bits_per_component != 8:
            raise ValueError('PDF only supports JPEG files with 8 bits '
                             'per component')
        colorspace = Name(self.COLOR_SPACE[num_components])
        super().__init__(width, height, colorspace, bits_per_component,
                         filter=DCTDecode())
        self._file.seek(0)
        self._data.write(self._file.read())

    read_uchar = create_reader('B')

    read_ushort = create_reader('H')

    def _set_density(self, density):
        if density is None:
            return
        x_density, y_density, unit = density
        if unit == DPI:
            self.dpi = x_density, y_density
        elif unit == DPCM:
            self.dpi = 2.54 * x_density, 2.54 * y_density

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
                density = self._parse_jfif_segment(header_length)
                self._set_density(density)
            elif marker == 0xE1:
                density = self._parse_exif_segment(header_length)
                self._set_density(density)
            elif (marker & 0xF0) == 0xC0 and marker not in (0xC4, 0xC8, 0xCC):
                v_size, h_size, bits_per_component, num_components = \
                    self._parse_start_of_frame(header_length)
                break
            else:
                self._file.seek(header_length - 2, SEEK_CUR)
        return h_size, v_size, bits_per_component, num_components

    JFIF_HEADER = create_reader('5s 2s B H H B B', lambda tuple: tuple)
    JFIF_UNITS = {0: None,
                  1: DPI,
                  2: DPCM}

    def _parse_jfif_segment(self, header_length):
        (identifier, version, units,
         h_density, v_density, h_thumbnail, v_thumbnail) = self.JFIF_HEADER()
        assert identifier == b'JFIF\0'
        thumbnail_size = 3 * h_thumbnail * v_thumbnail
        assert header_length == 16 + thumbnail_size
        return h_density, v_density, self.JFIF_UNITS[units]

    EXIF_HEADER = create_reader('5s B', lambda tuple: tuple)
    EXIF_TIFF_HEADER = 'H I'
    EXIF_TAG_FORMAT = 'H H I 4s'
    EXIF_ENDIAN = {0x4949: '<',
                   0x4D4D: '>'}

    EXIF_X_RESOLUTION = 0x11A
    EXIF_Y_RESOLUTION = 0x11B
    EXIF_RESOLUTION_UNIT = 0x128

    EXIF_TAG_TYPE = {1: 'B',
                     2: 's',
                     3: 'H',
                     4: 'I',
                     5: 'II',  # FIXME: becomes '<count>II'
                     7: 's',
                     9: 'i',
                     10: 'ii'}
    EXIF_UNITS = {2: DPI,
                  3: DPCM}

    def _parse_exif_segment(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        identifier, null = self.EXIF_HEADER()
        if identifier != b'Exif\0':
            self._file.seek(resume_position)
            return None
        assert null == 0
        tiff_header_offset = self._file.tell()
        byte_order = self.read_ushort()
        endian = self.EXIF_ENDIAN[byte_order]
        read_ushort = create_reader('H', endian=endian)

        def get_value(type, count, value_or_offset):
            value_format = self.EXIF_TAG_TYPE[type]
            num_bytes = count * calcsize(value_format)
            if num_bytes > 4:  # offset
                saved_offset = self._file.tell()
                offset, = unpack(endian + 'I', value_or_offset)
                self._file.seek(tiff_header_offset + offset)
                data = self._file.read(num_bytes)
                format = '{}{}{}'.format(endian, count, value_format)
                self._file.seek(saved_offset)
            else:
                format = endian + value_format
                data = value_or_offset[:calcsize(format)]

            raw_value = unpack(format, data)
            if type in (1, 3, 4, 9):
                value, = raw_value
            elif type == 2:
                value = raw_value[0].decode('ISO-8859-1')
            elif type in (5, 10):
                numerator, denomenator = raw_value
                value = numerator / denomenator
            elif type == 7:
                value = raw_value
            return value

        tiff_header = create_reader(self.EXIF_TIFF_HEADER,
                                    lambda tuple: tuple, endian)
        fortytwo, ifd_offset = tiff_header(self)
        assert fortytwo == 42
        self._file.seek(tiff_header_offset + ifd_offset)
        tag_format = create_reader(self.EXIF_TAG_FORMAT,
                                   lambda tuple: tuple, endian)
        num_tags = read_ushort(self)
        for i in range(num_tags):
            tag, type, count, value_or_offset = tag_format(self)
            value = get_value(type, count, value_or_offset)
            if tag == self.EXIF_X_RESOLUTION:
                x_resolution = value
            elif tag == self.EXIF_Y_RESOLUTION:
                y_resolution = value
            elif tag == self.EXIF_RESOLUTION_UNIT:
                resolution_unit = value
        self._file.seek(resume_position)
        return x_resolution, y_resolution, self.EXIF_UNITS[resolution_unit]

    SOF_HEADER = create_reader('B H H B', lambda tuple: tuple)

    def _parse_start_of_frame(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        sample_precision, v_size, h_size, num_components = self.SOF_HEADER()
        self._file.seek(resume_position)
        return v_size, h_size, sample_precision, num_components
