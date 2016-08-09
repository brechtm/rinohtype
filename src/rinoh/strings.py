# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .text import StyledText, SingleStyledTextBase
from .util import NamedDescriptor, WithNamedDescriptors


__all__ = ['String', 'Strings', 'StringField']


class String(NamedDescriptor):
    """Descriptor used to describe a configurable string"""
    def __init__(self, default_value, description):
        self.default_value = default_value
        self.description = description
        self.name = None

    def __get__(self, style, type=None):
        try:
            return style.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, style, value):
        if not StyledText.check_type(value):
            raise TypeError('The {} style attribute only accepts styled text'
                            .format(self.name))
        style[self.name] = value

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)\n'
                ':default: {}'
                .format(self.description, self.accepted_type.__name__,
                        self.default_value))


class Strings(dict, metaclass=WithNamedDescriptors):
    def __init__(self, **options):
        for name, value in options.items():
            string_descriptor = getattr(type(self), name, None)
            if not isinstance(string_descriptor, String):
                raise AttributeError('Unsupported page template option: {}'
                                     .format(name))
            setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)


class StringField(SingleStyledTextBase):
    def __init__(self, strings_class, key, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.strings_class = strings_class
        self.key = key

    def string(self, document):
        return document.strings(self.strings_class)[self.key]

    def text(self, flowable_target):
        string = self.string(flowable_target.document)
        try:
            return string.to_string(flowable_target)
        except AttributeError:
            return string
