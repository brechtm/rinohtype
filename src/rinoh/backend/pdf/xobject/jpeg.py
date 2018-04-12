# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from io import SEEK_CUR
from pathlib import Path
from struct import Struct, unpack, calcsize
from warnings import warn

from ..cos import Name, Array, Stream, Integer
from ..filter import DCTDecode, FlateDecode

from . import XObjectImage, DEVICE_GRAY, DEVICE_RGB, DEVICE_CMYK
from .icc import SRGB, UNCALIBRATED, get_icc_stream


__all__ = ['JPEGReader']


def create_reader(data_format, process_struct=lambda data: data[0], endian='>'):
    data_struct = Struct(endian + data_format)
    def reader(jpeg_reader):
        data = data_struct.unpack(jpeg_reader._file.read(data_struct.size))
        return process_struct(data)
    return reader


# useful resources
# * http://fileformats.archiveteam.org/wiki/JPEG
# * libjpeg.txt from the Independent JPEG Group's reference implementation
# * http://www.ozhiker.com/electronics/pjmt/jpeg_info/app_segments.html
# * http://www.w3.org/Graphics/JPEG/
# * http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf

class JPEGReader(XObjectImage):
    COLOR_SPACE = {1: DEVICE_GRAY,
                   3: DEVICE_RGB,
                   4: DEVICE_CMYK}

    def __init__(self, file_or_filename):
        try:
            self.filename = Path(file_or_filename)
            self._file = self.filename.open('rb')
        except TypeError:
            self.filename = None
            self._file = file_or_filename
        (width, height, bits_per_component, num_components, exif_color_space,
         icc_profile, adobe_color_transform, dpi) = self._get_metadata()
        if bits_per_component != 8:
            raise ValueError('PDF only supports JPEG files with 8 bits '
                             'per component')
        device_color_space = self.COLOR_SPACE[num_components]
        if icc_profile is None and exif_color_space is not UNCALIBRATED:
            icc_profile = get_icc_stream(exif_color_space)
        if icc_profile is not None:
            icc_profile['N'] = Integer(num_components)
            icc_profile['Alternate'] = device_color_space
            colorspace = Array([Name('ICCBased'), icc_profile])
        else:
            colorspace = device_color_space
        super().__init__(width, height, colorspace, bits_per_component, dpi,
                         filter=DCTDecode())
        if adobe_color_transform and num_components == 4:  # invert CMYK colors
            self['Decode'] = Array([Integer(1), Integer(0)] * 4)
        self._file.seek(0)
        while True:
            buffer = self._file.read(512 * 1024)  # 512 KB
            if not buffer:
                break
            self._data.write(buffer)

    read_uchar = create_reader('B')

    read_ushort = create_reader('H')

    def _density(self, density):
        if density is None:
            return None
        x_density, y_density, unit = density
        if unit == DPI:
            dpi = x_density, y_density
        elif unit == DPCM:
            dpi = 2.54 * x_density, 2.54 * y_density
        else:  # unit is None
            dpi = None
        return dpi

    def _get_metadata(self):
        dpi = None
        icc_profile = None
        exif_color_space = UNCALIBRATED
        next_icc_part_number = 1
        num_icc_parts = 0
        adobe_color_xform = None

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
                dpi = self._density(density)
            elif marker == 0xE1:
                result = self._parse_exif_segment(header_length)
                if result:
                    density, exif_color_space = result
                    dpi = self._density(density)
            elif marker == 0xE2:
                icc_part_number, num_icc_parts, icc_part_bytes = \
                    self._parse_icc_segment(header_length)
                assert icc_part_number == next_icc_part_number
                next_icc_part_number += 1
                if icc_profile is None:
                    assert icc_part_number == 1
                    icc_profile = Stream(filter=FlateDecode())
                icc_profile.write(icc_part_bytes)
            elif marker == 0xEE:
                adobe_color_xform = self._parse_adobe_dct_segment(header_length)
            elif (marker & 0xF0) == 0xC0 and marker not in (0xC4, 0xC8, 0xCC):
                v_size, h_size, bits_per_component, num_components = \
                    self._parse_start_of_frame(header_length)
                break
            else:
                self._file.seek(header_length - 2, SEEK_CUR)
        assert next_icc_part_number == num_icc_parts + 1
        return (h_size, v_size, bits_per_component, num_components,
                exif_color_space, icc_profile, adobe_color_xform, dpi)

    JFIF_HEADER = create_reader('5s 2s B H H B B', lambda tuple: tuple)

    def _parse_jfif_segment(self, header_length):
        (identifier, version, units,
         h_density, v_density, h_thumbnail, v_thumbnail) = self.JFIF_HEADER()
        assert identifier == b'JFIF\0'
        thumbnail_size = 3 * h_thumbnail * v_thumbnail
        assert header_length == 16 + thumbnail_size
        return h_density, v_density, JFIF_UNITS[units]

    EXIF_HEADER = create_reader('5s B', lambda tuple: tuple)
    EXIF_TIFF_HEADER = 'H I'
    EXIF_TAG_FORMAT = 'H H I 4s'

    def _parse_exif_segment(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        identifier, null = self.EXIF_HEADER()
        if identifier != b'Exif\0':
            self._file.seek(resume_position)
            return None
        assert null == 0
        tiff_header_offset = self._file.tell()
        byte_order = self.read_ushort()
        endian = EXIF_ENDIAN[byte_order]

        tiff_header = create_reader(self.EXIF_TIFF_HEADER,
                                    lambda tuple: tuple, endian)
        fortytwo, ifd_offset = tiff_header(self)
        assert fortytwo == 42
        self._file.seek(tiff_header_offset + ifd_offset)
        ifd_0th = self._parse_exif_ifd(endian, tiff_header_offset)
        color_space = UNCALIBRATED
        if EXIF_IFD_POINTER in ifd_0th:
            self._file.seek(tiff_header_offset + ifd_0th[EXIF_IFD_POINTER])
            ifd_exif = self._parse_exif_ifd(endian, tiff_header_offset)
            try:
                exif_color_space = ifd_exif[EXIF_COLOR_SPACE]
                color_space = EXIF_COLOR_SPACES[exif_color_space]
            except KeyError:
                warn('The EXIF table in "{}" is missing color space information'
                     .format(self.filename))
        density = (ifd_0th.get(EXIF_X_RESOLUTION, 72),
                   ifd_0th.get(EXIF_Y_RESOLUTION, 72),
                   EXIF_UNITS[ifd_0th.get(EXIF_RESOLUTION_UNIT, 2)])
        self._file.seek(resume_position)
        return density, color_space

    def _parse_exif_ifd(self, endian, tiff_header_offset):
        read_ushort = create_reader('H', endian=endian)
        tag_format = create_reader(self.EXIF_TAG_FORMAT,
                                   lambda tuple: tuple, endian)

        def get_value(type, count, value_or_offset):
            value_format = EXIF_TAG_TYPE[type]
            num_bytes = count * calcsize(value_format)
            if num_bytes > 4:  # offset
                saved_offset = self._file.tell()
                offset, = unpack(endian + 'I', value_or_offset)
                self._file.seek(tiff_header_offset + offset)
                data = self._file.read(num_bytes)
                format = '{}{}'.format(endian, count * value_format)
                self._file.seek(saved_offset)
            else:
                format = endian + value_format
                data = value_or_offset[:calcsize(format)]

            raw_value = unpack(format, data)
            if type in (1, 3, 4, 9):
                try:
                    value, = raw_value
                except ValueError:
                    value = raw_value
            elif type == 2:
                value = raw_value[0].decode('ISO-8859-1')
            elif type in (5, 10):
                try:
                    numerator, denomenator = raw_value
                    value = numerator / denomenator
                except ValueError:
                    pairs = zip(*(iter(raw_value), ) * 2)
                    value = tuple(num / denom for num, denom in pairs)
            elif type == 7:
                value = raw_value
            return value

        num_tags = read_ushort(self)
        result = {}
        for i in range(num_tags):
            tag, type, count, value_or_offset = tag_format(self)
            result[tag] = get_value(type, count, value_or_offset)
        return result

    ICC_HEADER = create_reader('12s B B', lambda tuple: tuple)

    def _parse_icc_segment(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        identifier, part_number, num_parts = self.ICC_HEADER()
        if identifier != b'ICC_PROFILE\0':
            self._file.seek(resume_position)
            return None
        part_bytes = self._file.read(resume_position - self._file.tell())
        return part_number, num_parts, part_bytes

    ADOBE_DCT_HEADER = create_reader('5s H H H B', lambda tuple: tuple)

    def _parse_adobe_dct_segment(self, header_length):
        assert header_length >= 14
        resume_position = self._file.tell() + header_length - 2
        identifier, version, flags1, flags2, color_transform = \
            self.ADOBE_DCT_HEADER()
        if identifier != b'Adobe':
            self._file.seek(resume_position)
            return None
        self._file.seek(resume_position)
        return ADOBE_COLOR_TRANSFORM[color_transform]

    SOF_HEADER = create_reader('B H H B', lambda tuple: tuple)

    def _parse_start_of_frame(self, header_length):
        resume_position = self._file.tell() + header_length - 2
        sample_precision, v_size, h_size, num_components = self.SOF_HEADER()
        self._file.seek(resume_position)
        return v_size, h_size, sample_precision, num_components


DPCM = 'dpcm'
DPI = 'dpi'

JFIF_UNITS = {0: None,
              1: DPI,
              2: DPCM}


EXIF_ENDIAN = {0x4949: '<',
               0x4D4D: '>'}
EXIF_TAG_TYPE = {1: 'B',
                 2: 's',
                 3: 'H',
                 4: 'I',
                 5: 'II',
                 7: 's',
                 9: 'i',
                 10: 'ii'}
EXIF_UNITS = {2: DPI,
              3: DPCM}
EXIF_COLOR_SPACES = {1: SRGB,
                     0xFFFF: UNCALIBRATED}

EXIF_X_RESOLUTION = 0x11A
EXIF_Y_RESOLUTION = 0x11B
EXIF_RESOLUTION_UNIT = 0x128
EXIF_IFD_POINTER = 0x8769

EXIF_COLOR_SPACE = 0xA001


UNKNOWN = 'RGB or CMYK'
YCC = 'YCbCr'
YCCK = 'YCCK'

ADOBE_COLOR_TRANSFORM = {0: UNKNOWN,
                         1: YCC,
                         2: YCCK}
