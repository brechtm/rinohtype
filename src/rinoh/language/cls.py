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
    """Collects localized strings for a particular language

    Args:
        code (str): short code identifying the language
        name (str): native name of the language

    """

    languages = {}  #: Dictionary mapping codes to :class:`Language`\ s

    def __init__(self, code, name):
        self.languages[code] = weakref.ref(self)
        self.code = code
        self.name = name
        self.strings = {}

    def __repr__(self):
        return "{}('{}', '{}')".format(type(self).__name__,
                                       self.code, self.name)

    def __contains__(self, item):
        assert isinstance(item, StringCollection)
        strings_class = type(item)
        assert strings_class not in self.strings
        self.strings[strings_class] = item

    @classmethod
    def parse_string(cls, string, source):
        return cls.languages[string]()

    @classmethod
    def doc_repr(cls, value):
        return ':data:`~.rinoh.language.{}` ({})'.format(value.code.upper(),
                                                         value.name)

    @classmethod
    def doc_format(cls):
        return ('the code of one of the '
                ':ref:`supported languages <supported_languages>`')
