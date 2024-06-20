# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import weakref

from ..attribute import AttributeType


__all__ = ['Language']


class Language(AttributeType):
    """Collects localized strings for a particular language

    Args:
        code (str): short code identifying the language
        name (str): native name of the language

        paragraph: label for referencing paragraphs
        section: label for referencing sections
        chapter: label for top-level sections
        figure: caption label for figures
        table: caption label for tables
        listing: caption label for (source code) listings
        contents: title for the table of contents section
        list_of_figures: title for the list of figures section
        list_of_tables: title for the list of tables section
        index: title for the index section

        attention: title for attention admonitions
        caution: title for caution admonitions
        danger: title for danger admonitions
        error: title for error admonitions
        hint: title for hint admonitions
        important: title for important admonitions
        note: title for note admonitions
        tip: title for tip admonitions
        warning: title for warning admonitions
        seealso: title for see-also admonitions

    """

    languages = {}  #: Dictionary mapping codes to :class:`Language`\ s

    def __init__(self, code, name, **localized_strings):
        self.languages[code] = weakref.ref(self)
        self.code = code
        self.name = name
        self.strings = localized_strings
        self.no_break_after = []

    def __repr__(self):
        return "{}('{}', '{}')".format(type(self).__name__,
                                       self.code, self.name)

    @classmethod
    def parse_string(cls, string, source):
        return cls.languages[string.lower()]()

    @classmethod
    def doc_repr(cls, value):
        return ':data:`~.rinoh.language.{}` ({})'.format(value.code.upper(),
                                                         value.name)

    @classmethod
    def doc_format(cls):
        return ('the code of one of the '
                ':ref:`supported languages <supported_languages>`')
