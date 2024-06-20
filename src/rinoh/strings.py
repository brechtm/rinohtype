# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from itertools import chain

from .attribute import AcceptNoneAttributeType
from .text import StyledText, SingleStyledText, MixedStyledTextBase
from .util import NamedDescriptor, WithNamedDescriptors


__all__ = ['Strings', 'StringField']


class Strings(AcceptNoneAttributeType):
    """Stores several :class:`StringCollection`\\ s"""

    def __init__(self):
        self.builtin = {}
        self.user = {}

    def __setitem__(self, identifier, value):
        symbol = identifier[0]
        if symbol not in '@$':
            raise ValueError("A string identifier need to start with @, for "
                             "builtin strings, or $ for user-defined strings")
        key = identifier[1:]
        if symbol == '@':
            self.set_builtin_string(key, value)
        else:
            self.set_user_string(key, value)

    def set_builtin_string(self, key, value):
        self.builtin[key] = value

    def set_user_string(self, key, value):
        self.user[key] = value

    @classmethod
    def doc_format(cls):
        return "strings need to be entered in INI in a section named 'STRINGS'"


class StringField(MixedStyledTextBase):
    """Styled text that will be substituted with a configured string

    The displayed string is either the localized string as determined by the
    language set for the document or the user-supplied string passed to the
    :class:`.TemplateConfiguration`.

    """
    def __init__(self, key, style=None, parent=None, source=None, user=False):
        super().__init__(style=style, parent=parent, source=source)
        self.key = key
        self.user = user

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __str__(self):
        result = "'{{{}{}}}'".format('$' if self.user else '@', self.key)
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def __repr__(self):
        return ("{}({!r}, style={})"
                .format(type(self).__name__, self.key, self.style))

    @classmethod
    def parse_string(cls, string, style=None):
        return cls(string[1:], style=style, user=string[0] == '$')

    def copy(self, parent=None):
        return type(self)(self.key, style=self.style, parent=parent,
                          source=self.source, user=self.user)

    def children(self, container):
        text = container.document.get_string(self.key, self.user)
        if isinstance(text, StyledText):
            text.parent = self
            yield text
        else:
            yield SingleStyledText(text, parent=self)
