# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .text import StyledText
from .util import NamedDescriptor, WithNamedDescriptors


__all__ = ['String', 'Strings']


class String(NamedDescriptor):
    """Descriptor used to describe a style attribute"""
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
