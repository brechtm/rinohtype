# This file is part of RinohType, the Python document preparation system.
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

    def __init__(self, width, height, colorspace, bitspercomponent,
                 filter=None):
        super().__init__(filter=filter)
        self['Width'] = Integer(width)
        self['Height'] = Integer(height)
        self['ColorSpace'] = colorspace
        self['BitsPerComponent'] = Integer(bitspercomponent)

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
