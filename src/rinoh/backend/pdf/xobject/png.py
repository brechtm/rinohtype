# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from io import BytesIO
from itertools import islice
from pathlib import Path
from struct import Struct, pack

from . import purepng

from ..cos import Array, Integer, Stream, Name, Dictionary, Real
from ..filter import FlateDecode, FlateDecodeParams

from . import (XObjectImage, DEVICE_GRAY, DEVICE_RGB, INDEXED, PERCEPTUAL,
               ABSOLUTE_COLORIMETRIC, RELATIVE_COLORIMETRIC, SATURATION)
from .icc import get_icc_stream, SRGB


__all__ = ['PNGReader']


class PNGReader(XObjectImage):
    def __init__(self, file_or_filename):
        png = purepng.Reader(str(file_or_filename)
                             if isinstance(file_or_filename, Path)
                             else file_or_filename)
        try:
            png.preamble()
        except purepng.FormatError as format_error:
            raise ValueError(*format_error.args)
        assert png.compression == 0
        assert png.filter == 0
        assert png.interlace == 0
        color_params = FlateDecodeParams(predictor=10, colors=png.color_planes,
                                         bits_per_component=png.bitdepth,
                                         columns=png.width)
        super().__init__(png.width, png.height, self._colorspace(png),
                         png.bitdepth, self._dpi(png),
                         filter=FlateDecode(color_params))
        if png.rendering_intent is not None:
            self['Intent'] = RENDERING_INTENT[png.rendering_intent]
        if png.alpha:  # grayscale/RGB with alpha channel
            smask_params = FlateDecodeParams(predictor=10, colors=1,
                                             bits_per_component=png.bitdepth,
                                             columns=png.width)
            self['SMask'] = XObjectImage(png.width, png.height, DEVICE_GRAY,
                                         png.bitdepth,
                                         filter=FlateDecode(smask_params))
            for color_row, alpha_row in self._split_color_alpha(png):
                self.write(color_row, bypass_predictor=True)
                self['SMask'].write(alpha_row, bypass_predictor=True)
        else:
            for idat_chunk in png.idat():
                self.write_raw(idat_chunk)
            if png.trns:
                if png.plte:  # alpha values assigned to palette colors
                    # TODO: if only a single color has trn 0, go to else
                    self['SMask'] = XObjectImage(png.width, png.height,
                                                 DEVICE_GRAY, 8,
                                                 filter=FlateDecode())
                    for alpha_row in self._plte_index_to_alpha(png):
                        self['SMask'].write(alpha_row)
                else:  # a single color is transparent
                    values = (value for value in png.transparent
                              for _ in range(2))
                    self['Mask'] = Array(Integer(value) for value in values)

    def _dpi(self, png):
        try:
            (x_density, y_density), unit = png.resolution
            if unit == 0:
                return x_density / y_density   # pixel aspect ratio
            elif unit == 1:
                return x_density / 100 * 2.54, y_density / 100 * 2.54
        except AttributeError:
            return None

    def _colorspace(self, png):
        device_color_space = COLOR_SPACE[png.color_type & 3]
        icc_profile = self._icc_profile(png)
        if icc_profile is None and png.rendering_intent is not None:
            icc_profile = get_icc_stream(SRGB)
        if icc_profile is not None:
            icc_profile['N'] = Integer(3 if device_color_space == DEVICE_RGB
                                       else 1)
            icc_profile['Alternate'] = device_color_space
            colorspace = Array([Name('ICCBased'), icc_profile])
        else:
            def cal_chromaticity(cal_colorspace, white, red, green, blue):
                xyz = chromaticity_to_XYZ(white, red, green, blue)
                white_xyz, a_xyz, b_xyz, c_xyz = xyz
                cal_colorspace['WhitePoint'] = Array([Real(value) for value
                                                      in white_xyz])
                if device_color_space == DEVICE_RGB:
                    cal_colorspace['Matrix'] = Array([Real(value) for x_y_z
                                                      in (a_xyz, b_xyz, c_xyz)
                                                      for value in x_y_z])

            cal_colorspace = {}
            if hasattr(png, 'gamma') and png.gamma != 0:
                gamma = Real(1 / png.gamma)
                cal_colorspace['Gamma'] = (Array([gamma] * 3)
                                           if device_color_space == DEVICE_RGB
                                           else gamma)
            if hasattr(png, 'white_point'):
                cal_chromaticity(cal_colorspace, png.white_point,
                                 *png.rgb_points)
            # TODO: assume sRGB if no color profile is set?
            if cal_colorspace:
                if 'WhitePoint' not in cal_colorspace:
                    # assume sRGB chromaticity
                    cal_chromaticity(cal_colorspace, *SRGB_CHROMATICITIES)
                cal_type = (Name('CalGray')
                            if device_color_space == DEVICE_GRAY
                            else Name('CalRGB'))
                colorspace = Array([cal_type, Dictionary(**cal_colorspace)])
            else:
                colorspace = device_color_space
        if png.colormap:  # palette
            num_entries = len(png.plte) // 3
            palette_stream = Stream(filter=FlateDecode())
            palette_stream.write(png.plte)
            colorspace = Array([INDEXED, colorspace,
                                Integer(num_entries - 1), palette_stream])
        return colorspace

    def _icc_profile(self, png):
        if hasattr(png, 'icc_profile'):
            icc_profile = Stream(filter=FlateDecode())
            icc_profile_name, icc_profile_data = png.icc_profile
            icc_profile.write(icc_profile_data)
            return icc_profile
        else:
            return None

    def _split_color_alpha(self, png):
        bytedepth = png.bitdepth // 8
        num_color_bytes = png.color_planes * bytedepth
        idat = BytesIO()
        for idat_chunk in png.idatdecomp():
            idat.write(idat_chunk)
        row_num_bytes = 1 + (png.color_planes + 1) * bytedepth * png.width
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
            yield bytes(color_values), bytes(alpha_values)
        assert idat.read() == b''

    def _plte_index_to_alpha(self, png):
        num_entries = len(png.plte) // 3
        frm = b''.join(pack('B', i) for i in range(num_entries))
        to = (b''.join(pack('B', alpha) for alpha in png.trns)
              + b'\xFF' * (num_entries - len(png.trns)))
        trans = bytearray.maketrans(frm, to)
        rows = (self.read(png.row_bytes) for _ in range(png.height))
        if png.bitdepth < 8:
            rows = to_8bit_per_pixel(rows, png.bitdepth, png.width)
        for row_bytes in rows:
            yield row_bytes.translate(trans)
        assert self.read() == b''
        self.reset()


COLOR_SPACE = {0: DEVICE_GRAY,
               2: DEVICE_RGB,
               3: DEVICE_RGB}

RENDERING_INTENT = {purepng.ABSOLUTE_COLORIMETRIC: ABSOLUTE_COLORIMETRIC,
                    purepng.RELATIVE_COLORIMETRIC: RELATIVE_COLORIMETRIC,
                    purepng.SATURATION: SATURATION,
                    purepng.PERCEPTUAL: PERCEPTUAL}

# from ITU-R Recommendation BT.709-5
SRGB_CHROMATICITIES = (0.3127, 0.329), (0.64, 0.33), (0.3, 0.6), (0.15, 0.06)

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


def chromaticity_to_XYZ(white, red, green, blue):
    """From the "CalRGB Color Spaces" section of "PDF Reference", 6th ed."""
    xW, yW = white
    xR, yR = red
    xG, yG = green
    xB, yB = blue
    R = G = B = 1.0

    z = yW * ((xG - xB) * yR - (xR - xB) * yG + (xR - xG) * yB)
    YA = yR / R  * ((xG - xB) * yW - (xW - xB) * yG + (xW - xG) * yB) / z
    XA = YA * xR / yR
    ZA = YA * ((1 - xR) / yR - 1)
    YB = - yG / G * ((xR - xB) * yW - (xW - xB) * yR + (xW - xR) * yB) / z
    XB = YB * xG / yG
    ZB = YB * ((1 - xG) / yG - 1)
    YC = yB / B * ((xR - xG) * yW - (xW - xG) * yR + (xW - xR) * yG) / z
    XC = YC * xB / yB
    ZC = YC * ((1 - xB) / yB - 1)
    XW = XA * R + XB * G + XC * B
    YW = YA * R + YB * G + YC * B
    ZW = ZA * R + ZB * G + ZC * B

    return (XW, YW, ZW), (XA, YA, ZA), (XB, YB, ZB), (XC, YC, ZC)
