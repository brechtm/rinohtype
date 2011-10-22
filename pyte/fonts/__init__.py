"""Predefined fonts"""

import os

from .. import __file__ as pyte_file


__all__ = ['adobe14', 'adobe35']

pyte_path = os.path.abspath(os.path.dirname(pyte_file))
fonts_path = os.path.join(pyte_path, 'data', 'fonts')
