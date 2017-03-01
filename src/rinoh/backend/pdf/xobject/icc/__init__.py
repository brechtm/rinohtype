# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import os

from ...filter import FlateDecode
from ...cos import Stream


__all__ = ['get_icc_stream', 'SRGB', 'ADOBERGB', 'UNCALIBRATED']


SRGB = 'sRGB'
ADOBERGB = 'AdobeRGB'
UNCALIBRATED = None

ICC_PATH = os.path.abspath(os.path.dirname(__file__))
ICC_FILENAME = {SRGB: 'sRGB_IEC61966-2-1_black_scaled.icc',
                ADOBERGB: None}   # TODO
ICC_DATA = {}


def get_icc_stream(color_space):
    icc_stream = Stream(filter=FlateDecode())
    try:
        data = ICC_DATA[color_space]
    except KeyError:
        icc_file_path = os.path.join(ICC_PATH, ICC_FILENAME[color_space])
        stream = Stream(filter=FlateDecode())
        with open(icc_file_path, 'rb') as icc:
            stream.write(icc.read())
        stream.reset()
        data = ICC_DATA[color_space] = stream._data
    icc_stream._data = data
    return icc_stream
