# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""rinohtype


"""

import os

from importlib import import_module

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata


CORE_MODULES = ['annotation', 'attribute', 'color', 'dimension', 'document',
                'draw', 'element', 'flowable', 'glossary', 'highlight',
                'image', 'index', 'inline', 'layout', 'number', 'paper',
                'paragraph', 'reference', 'structure', 'style', 'table',
                'template', 'text']

__all__ = CORE_MODULES + ['font', 'fonts', 'frontend', 'backend', 'resource',
                          'styleds', 'styles', 'stylesheets', 'templates',
                          'strings', 'language']


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


__version__ = importlib_metadata.version('rinohtype')
__release_date__ = '2021-02-03'


from . import resource

# create proxies for the core classes/constants at the top level for easy access
for name in CORE_MODULES:
    module = import_module('.' + name, __name__)
    module_dict, module_all = module.__dict__, module.__all__
    globals().update({name: module_dict[name] for name in module_all})
    __all__ += module_all


register_template = resource._DISTRIBUTION.register_template
register_typeface = resource._DISTRIBUTION.register_typeface

# list all StringCollection subclasses in its docstring
_ = ['* :class:`.{}`'.format(subclass_name)
     for subclass_name in sorted(strings.StringCollection.subclasses)]
strings.StringCollection.__doc__ += ('\n\n    :Subclasses: '
                                     + '\n                 '.join(_))
