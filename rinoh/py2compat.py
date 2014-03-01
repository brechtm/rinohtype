
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import locale
import sys


__all__ = ['PY2']


PY2 = sys.version_info < (3, 0)

if PY2:
    __all__ += ['str', 'print', 'open', 'super', 'chr', 'py2str']

    from io import open
    from .magicsuper import super
    py2str = str
    str = unicode
    std_print = print
    chr = unichr
    def print(*objects, **kwargs):
        if kwargs.get('file', sys.stdout) == sys.stdout:
            objects = (unicode(obj) for obj in objects)
            if not sys.stdout.encoding:
                objects = (obj.encode(locale.getpreferredencoding())
                           for obj in objects)
        std_print(*objects, **kwargs)
