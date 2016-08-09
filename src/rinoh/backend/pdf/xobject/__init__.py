# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..cos import Name, Integer, Stream


__all__ = ['XObject', 'XObjectForm', 'XObjectImage']


class XObject(Stream):
    type = 'XObject'


class XObjectForm(XObject):
    subtype = 'Form'

    def __init__(self, bounding_box):
        super().__init__()
        self['BBox'] = bounding_box


class XObjectImage(XObject):
    subtype = 'Image'

    DEFAULT_DPI = 72

    def __init__(self, width, height, colorspace, bitspercomponent,
                 dpi_or_aspect_ratio=None, filter=None):
        super().__init__(filter=filter)
        self['Width'] = Integer(width)
        self['Height'] = Integer(height)
        self['ColorSpace'] = colorspace
        self['BitsPerComponent'] = Integer(bitspercomponent)
        if dpi_or_aspect_ratio is None:
            self.dpi = (self.DEFAULT_DPI, self.DEFAULT_DPI)
        else:
            try:  # horizontal and vertical DPI
                self.dpi = _, _ = dpi_or_aspect_ratio
            except TypeError:  # pixel aspect ratio
                ar = dpi_or_aspect_ratio
                self.dpi = ((self.DEFAULT_DPI, self.DEFAULT_DPI / ar) if ar > 1
                            else (self.DEFAULT_DPI * ar, self.DEFAULT_DPI))

    @property
    def width(self):
        """Width of this image in postscript points"""
        dpi_x, dpi_y = self.dpi
        return self['Width'] / dpi_x * 72

    @property
    def height(self):
        """Height of this image in postscript points"""
        dpi_x, dpi_y = self.dpi
        return self['Height'] / dpi_y * 72


# color spaces
DEVICE_GRAY = Name('DeviceGray')
DEVICE_RGB = Name('DeviceRGB')
DEVICE_CMYK = Name('DeviceCMYK')
INDEXED = Name('Indexed')

# rendering intents
ABSOLUTE_COLORIMETRIC = Name('AbsoluteColorimetric')
RELATIVE_COLORIMETRIC = Name('RelativeColorimetric')
SATURATION = Name('Saturation')
PERCEPTUAL = Name('Perceptual')
