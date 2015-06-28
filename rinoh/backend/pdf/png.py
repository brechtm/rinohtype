# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from io import BytesIO
from itertools import islice

import png as purepng

from struct import Struct, pack

from .cos import (Name, XObjectImage, Array, Integer, Stream,
                  DEVICE_GRAY, DEVICE_RGB, INDEXED)
from .filter import FlateDecode, FlateDecodeParams


__all__ = ['PNGReader']


class PNGReader(XObjectImage):
    COLOR_SPACE = {0: DEVICE_GRAY,
                   2: DEVICE_RGB,
                   3: INDEXED}

    def __init__(self, file_or_filename):
        print('PNGReader:', file_or_filename)
        png = purepng.Reader(file_or_filename)
        png.preamble()
        assert png.compression == 0
        assert png.filter == 0
        assert png.interlace == 0
        try:
            (x_density, y_density), unit = png.resolution
            self.dpi = x_density / 100 * 2.54, y_density / 100 * 2.54
        except AttributeError:
            self.dpi = 72, 72
        colorspace = self.COLOR_SPACE[png.color_type & 3]
        if png.colormap:  # palette
            num_entries = len(png.plte) // 3
            palette_stream = Stream(filter=FlateDecode())
            palette_stream.write(png.plte)
            colorspace = Array([colorspace, DEVICE_RGB,
                                Integer(num_entries - 1), palette_stream])
        flate_params = FlateDecodeParams(predictor=10, colors=png.color_planes,
                                         bits_per_component=png.bitdepth,
                                         columns=png.width)
        super().__init__(png.width, png.height, colorspace, png.bitdepth,
                         filter=FlateDecode())
        if png.alpha:  # grayscale/RGB with alpha channel
            num_color_comps = 1 if png.color_type == 4 else 3
            bytedepth = png.bitdepth // 8
            num_color_bytes = num_color_comps * bytedepth
            idat = BytesIO()
            for idat_chunk in png.idatdecomp():
                idat.write(idat_chunk)
            self['SMask'] = XObjectImage(png.width, png.height,
                                         Name('DeviceGray'), png.bitdepth,
                                         filter=FlateDecode())
            row_num_bytes = 1 + (num_color_comps + 1) * bytedepth * png.width
            pixel_color_fmt = '{}B{}x'.format(num_color_bytes, bytedepth)
            pixel_alpha_fmt = '{}x{}B'.format(num_color_bytes, bytedepth)
            row_color_struct = Struct('B' + pixel_color_fmt * png.width)
            row_alpha_struct = Struct('B' + pixel_alpha_fmt * png.width)
            idat.seek(0)
            row_bytes = bytearray(row_num_bytes)
            for i in range(png.height):
                idat.readinto(row_bytes)
                color_values = row_color_struct.unpack(row_bytes)
                alpha_values = row_alpha_struct.unpack(row_bytes)
                self.write(bytes(color_values))
                self['SMask'].write(bytes(alpha_values))
            assert idat.read() == b''
            smask_params = FlateDecodeParams(predictor=10, colors=1,
                                             bits_per_component=png.bitdepth,
                                             columns=png.width)
            self['SMask'].filter.params = smask_params
        else:
            for idat_chunk in png.idat():
                self._data.write(idat_chunk)
            if png.trns:
                if png.plte:  # alpha values assigned to palette colors
                    frm = b''.join(pack('B', i) for i in range(num_entries))
                    to = (b''.join(pack('B', alpha) for alpha in png.trns)
                          + b'\xFF' * (num_entries - len(png.trns)))
                    trans = bytearray.maketrans(frm, to)
                    params = FlateDecodeParams(predictor=10, colors=1,
                                               bits_per_component=png.bitdepth,
                                               columns=png.width)
                    tmp = Stream(filter=FlateDecode(params))
                    tmp._data.write(self._data.getvalue())
                    self['SMask'] = XObjectImage(png.width, png.height,
                                                 Name('DeviceGray'), 8,
                                                 filter=FlateDecode())
                    rows = (tmp.read(png.row_bytes) for _ in range(png.height))
                    if png.bitdepth < 8:
                        rows = to_8bit_per_pixel(rows, png.bitdepth, png.width)
                    for row_bytes in rows:
                        self['SMask'].write(row_bytes.translate(trans))
                else:  # a single color is transparent
                    values = (value for value in png.transparent
                              for _ in range(2))
                    self['Mask'] = Array(Integer(value) for value in values)
        self.filter.params = flate_params


def to_8bit_per_pixel(rows, bitdepth, width):
    px_per_byte = 8 // bitdepth
    mask = 2**bitdepth - 1
    shft = [(i - 1) * bitdepth for i in range(px_per_byte, 0, -1)]

    row_buffer = bytearray(width)
    for row_bytes in rows:
        row_buffer[:] = islice(((byte >> shift) & mask
                                for byte in row_bytes
                                for shift in shft), width)
        yield row_buffer
