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


__all__ = ['String', 'StringCollection', 'Strings', 'StringField']


class String(NamedDescriptor):
    """Descriptor used to describe a configurable string

    Args:
        description (str): a short description for this string

    """

    def __init__(self, description):
        self.description = description
        self.name = None

    def __get__(self, strings, type=None):
        try:
            return strings.get(self.name)
        except AttributeError:
            return self

    def __set__(self, strings, value):
        if not StyledText.check_type(value):
            raise TypeError('String attributes only accept styled text'
                            .format(self.name))
        strings[self.name] = value


class StringCollectionMeta(WithNamedDescriptors):
    def __new__(metacls, classname, bases, cls_dict):
        cls = super().__new__(metacls, classname, bases, cls_dict)
        try:
            StringCollection.subclasses[classname] = cls
        except NameError:
            pass  # cls is StringCollection
        else:
            strings = []
            attrs = []
            for name, string in cls_dict.items():
                if not isinstance(string, String):
                    continue
                strings.append(string)
                attrs.append('{} (:class:`.{}`): {}'
                             .format(name, type(string).__name__,
                                     string.description))
            cls._strings = strings
            cls.__doc__ += ('\n        '
                            .join(chain(['\n\n    Attributes:'], attrs)))
        return cls


class StringCollection(dict, metaclass=StringCollectionMeta):
    """A collection of related configurable strings"""

    subclasses = {}

    def __init__(self, **strings):
        for name, value in strings.items():
            string_descriptor = getattr(type(self), name, None)
            if not isinstance(string_descriptor, String):
                raise AttributeError("'{}' is not an accepted string for {}"
                                     .format(name, type(self).__name__))
            setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)


class UserStrings(dict, metaclass=StringCollectionMeta):
    """Collection of user-specified strings

    Unlike other string collections, these are not limited to a predefined set.

    """

    def __init__(self, **strings):
        for name, value in strings.items():
            if not StyledText.check_type(value):
                raise TypeError('String attributes only accept styled text'
                                .format(self.name))
            self[name] = value


class Strings(AcceptNoneAttributeType, dict):
    """Stores several :class:`StringCollection`\\ s"""

    def __init__(self, *string_collections):
        for string_collection in string_collections:
            self[type(string_collection)] = string_collection

    def __setitem__(self, string_collection_class, string_collection):
        if string_collection_class in self:
            raise ValueError("{} is already registered with this {} instance"
                             .format(string_collection_class.__name__,
                                     type(self).__name__))
        super().__setitem__(string_collection_class, string_collection)

    def __missing__(self, string_collection_class):
        instance = string_collection_class()
        self[string_collection_class] = instance
        return instance

    @classmethod
    def doc_format(cls):
        return ('strings need to be entered in INI sections named after the '
                ':class:`.StringCollection` subclasses')


class StringField(MixedStyledTextBase):
    """Styled text that will be substituted with a configured string

    The displayed string is either the localized string as determined by the
    language set for the document or the user-supplied string passed to the
    :class:`.TemplateConfiguration`.

    """
    def __init__(self, strings_class, key, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.strings_class = strings_class
        self.key = key

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __str__(self):
        result = "'{{{}.{}}}'".format(self.strings_class.__name__, self.key)
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def __repr__(self):
        return ("{}({}, '{}', style={})"
                .format(type(self).__name__, self.strings_class.__name__,
                        self.key, self.style))

    @classmethod
    def parse_string(cls, string, style=None):
        collection, key = string.split('.')
        return cls(StringCollection.subclasses[collection], key, style=style)

    def children(self, container):
        text = container.document.get_string(self.strings_class, self.key)
        if isinstance(text, StyledText):
            text.parent = self
            yield text
        else:
            yield SingleStyledText(text, parent=self)
