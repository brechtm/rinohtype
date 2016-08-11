# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""rinohtype


"""

import os
import sys

from importlib import import_module

from .version import __version__, __release_date__


if sys.version_info < (3, 3):
    print('rinohtype requires Python 3.3 or higher')
    sys.exit(1)


CORE_MODULES = ['annotation', 'color', 'dimension', 'document', 'draw', 'float',
                'flowable', 'highlight', 'index', 'inline', 'layout', 'number',
                'paper', 'paragraph', 'reference', 'structure', 'style',
                'table', 'text']

__all__ = CORE_MODULES + ['font', 'frontend', 'backend', 'styleds', 'styles']


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


# create proxies for the core classes/constants at the top level for easy access
for name in CORE_MODULES:
    module = import_module('.' + name, __name__)
    module_dict, module_all = module.__dict__, module.__all__
    globals().update({name: module_dict[name] for name in module_all})
    __all__ += module_all
