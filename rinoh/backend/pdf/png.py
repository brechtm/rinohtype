# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from io import BytesIO
from itertools import chain, repeat

import png

from struct import Struct, pack

from .cos import Name, XObjectImage, Array, Integer, Stream
from .filter import FlateDecode, FlateDecodeParams

__all__ = ['PNGReader']


class PNGReader(XObjectImage):
    COLOR_SPACE = {0: 'DeviceGray',
                   2: 'DeviceRGB',
                   3: 'Indexed',
                   4: 'DeviceGray',
                   6: 'DeviceRGB'}
    NUM_COLOR_COMPONENTS = {0: 1,
                            2: 3,
                            4: 1,
                            6: 3}

    def __init__(self, file_or_filename):
        print('PNGReader:', file_or_filename)
        self._png = png.Reader(file_or_filename)
        self._png.preamble()
        assert self._png.compression == 0
        assert self._png.filter == 0
        assert self._png.interlace == 0
        try:
            (x_density, y_density), unit = self._png.resolution
            assert unit == 1
            self.dpi = x_density / 100 * 2.54, y_density / 100 * 2.54
        except AttributeError:
            self.dpi = 72, 72
        colorspace = Name(self.COLOR_SPACE[self._png.color_type])
        if str(colorspace) == 'Indexed':
            num_entries = len(self._png.plte) // 3
            palette_stream = Stream(filter=FlateDecode())
            palette_stream.write(self._png.plte)
            colorspace = Array([colorspace, Name('DeviceRGB'),
                                Integer(num_entries - 1), palette_stream])
            predictor_colors = 1
        else:
            predictor_colors = self.NUM_COLOR_COMPONENTS[self._png.color_type]
        flate_params = FlateDecodeParams(predictor=10, colors=predictor_colors,
                                         bits_per_component=self._png.bitdepth,
                                         columns=self._png.width)
        super().__init__(self._png.width, self._png.height, colorspace,
                         self._png.bitdepth, filter=FlateDecode())
        bitdepth = self._png.bitdepth
        if self._png.color_type in (4, 6):
            num_color_comps = 1 if self._png.color_type == 4 else 3
            bytedepth = self._png.bitdepth // 8
            num_color_bytes = num_color_comps * bytedepth
            idat = BytesIO()
            for idat_chunk in self._png.idatdecomp():
                idat.write(idat_chunk)
            self['SMask'] = XObjectImage(self._png.width, self._png.height,
                                         Name('DeviceGray'), self._png.bitdepth,
                                         filter=FlateDecode())
            row_num_bytes = 1 + (num_color_comps + 1) * bytedepth * self._png.width
            pixel_color_fmt = '{}B{}x'.format(num_color_bytes, bytedepth)
            pixel_alpha_fmt = '{}x{}B'.format(num_color_bytes, bytedepth)
            row_color_struct = Struct('B' + pixel_color_fmt * self._png.width)
            row_alpha_struct = Struct('B' + pixel_alpha_fmt * self._png.width)
            idat.seek(0)
            row_bytes = bytearray(row_num_bytes)
            for i in range(self._png.height):
                idat.readinto(row_bytes)
                color_values = row_color_struct.unpack(row_bytes)
                alpha_values = row_alpha_struct.unpack(row_bytes)
                self.write(bytes(color_values))
                self['SMask'].write(bytes(alpha_values))
            assert idat.read() == b''
            smask_filter_params = FlateDecodeParams(predictor=10, colors=1,
                                                    bits_per_component=bitdepth,
                                                    columns=self._png.width)
            self['SMask'].filter.params = smask_filter_params
        else:
            for idat_chunk in self._png.idat():
                self._data.write(idat_chunk)
            trns = self._png.trns
            if trns:
                if self._png.plte:
                    pixels_per_byte = 8 // bitdepth
                    frm = b''.join(pack('B', i) for i in range(num_entries))
                    to = (b''.join(pack('B', alpha) for alpha in trns)
                          + b'\xFF' * (num_entries - len(trns)))
                    trans = bytearray.maketrans(frm, to)
                    tmp_params = FlateDecodeParams(predictor=10, colors=1,
                                                   bits_per_component=bitdepth,
                                                   columns=self._png.width)
                    tmp = Stream(filter=FlateDecode(tmp_params))
                    tmp._data.write(self._data.getvalue())
                    self['SMask'] = XObjectImage(self._png.width,
                                                 self._png.height,
                                                 Name('DeviceGray'), bitdepth,
                                                 filter=FlateDecode())
                    for i in range(self._png.height):
                        row_bytes = tmp.read(self._png.row_bytes)
                        self['SMask'].write(row_bytes.translate(trans))
                else:
                    values = chain(*(repeat(value, 2)
                                     for value in self._png.transparent))
                    self['Mask'] = Array(Integer(value) for value in values)
        self.filter.params = flate_params
