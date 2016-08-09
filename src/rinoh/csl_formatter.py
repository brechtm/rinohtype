# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import GroupedFlowables
from .paragraph import Paragraph
from . import text


def preformat(text):
    return text


def factory(cls):
    def __init__(self, string):
        return super(self.__class__, self).__init__(str(string))
    space = {'__init__': __init__}
    return type(cls.__name__, (cls, ), space)


Italic = factory(text.Italic)
Oblique = factory(text.Italic)

Bold = factory(text.Bold)
Light = factory(text.Bold)

Underline = factory(text.Bold)

Superscript = factory(text.Superscript)
Subscript = factory(text.Subscript)

SmallCaps = factory(text.SmallCaps)
