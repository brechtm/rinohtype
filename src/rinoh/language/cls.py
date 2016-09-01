# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import weakref

from ..attribute import AttributeType
from ..strings import StringCollection


__all__ = ['Language']


class Language(AttributeType):
    languages = {}

    def __init__(self, code, name):
        self.languages[code] = weakref.ref(self)
        self.code = code
        self.name = name
        self.strings = {}

    def __contains__(self, item):
        assert isinstance(item, StringCollection)
        strings_class = type(item)
        assert strings_class not in self.strings
        self.strings[strings_class] = item

    @classmethod
    def parse_string(cls, string):
        return cls.languages[string]()
