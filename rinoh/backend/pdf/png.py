# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from io import BytesIO

import png

from .cos import Name, XObjectImage, Array, Integer, HexString
from .filter import FlateDecode, FlateDecodeParams

__all__ = ['PNGReader']


class PNGReader(XObjectImage):
    COLOR_SPACE = {0: 'DeviceGray',
                   2: 'DeviceRGB',
                   3: 'Indexed',
                   4: 'DeviceGray'}
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
            palette = self._png.palette('force')
            num_entries = len(palette)
            lookup = bytearray(3 * num_entries)
            for i, (r, g, b, a) in enumerate(palette):
                lookup[3 * i:3 * i + 3] = r, g, b
            colorspace = Array([colorspace, Name('DeviceRGB'),
                                Integer(num_entries - 1), HexString(lookup)])
            predictor_colors = self._png.bitdepth
        else:
            predictor_colors = self.NUM_COLOR_COMPONENTS[self._png.color_type]
        flate_params = FlateDecodeParams(predictor=10, colors=predictor_colors,
                                         bits_per_component=self._png.bitdepth,
                                         columns=self._png.width)
        super().__init__(self._png.width, self._png.height, colorspace,
                         self._png.bitdepth, filter=FlateDecode())
        if self._png.color_type == 4:
            idat = BytesIO()
            for idat_chunk in self._png.idatdecomp():
                idat.write(idat_chunk)
            idat.seek(0)
            self['SMask'] = XObjectImage(self._png.width, self._png.height,
                                         Name('DeviceGray'), 8, FlateDecode())
            while True:
                row = idat.read(1 + 2 * self._png.width)
                if not row:
                    break
                self.write(row[0:1] + row[1::2])
                self['SMask'].write(row[0:1] + row[2::2])
            soft_mask_filter_params = FlateDecodeParams(predictor=10, colors=1,
                                                        bits_per_component=8,
                                                        columns=self._png.width)
            self['SMask'].filter.params = soft_mask_filter_params
        else:
            for idat_chunk in self._png.idat():
                self._data.write(idat_chunk)
        self.filter.params = flate_params
