"""pyTe


"""

import os

from importlib import import_module


CORE_MODULES = ['dimension', 'document', 'draw', 'float', 'flowable', 'layout',
                'number', 'paper', 'paragraph', 'reference', 'structure',
                'style', 'text']

__all__ = CORE_MODULES + ['font', 'frontend', 'backend']


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


# create proxies for the core classes/constants at the top level for easy access
for name in CORE_MODULES:
    module = import_module('.' + name, __name__)
    for attr in module.__all__:
        globals()[attr] = getattr(module, attr)
