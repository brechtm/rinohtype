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

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)'
                .format(self.description, self.accepted_type.__name__))


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
    def __init__(self, strings_class, key, case=None, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.strings_class = strings_class
        self.key = key
        self.case = case or (lambda string: string)

    def __repr__(self):
        return "{}({}, '{}')".format(type(self).__name__,
                                     self.strings_class, self.key)

    def string(self, document):
        return document.get_string(self.strings_class, self.key)

    def text(self, flowable_target):
        if flowable_target is None:
            return repr(self)
        string = self.string(flowable_target.document)
        try:
            string = string.to_string(flowable_target)
        except AttributeError:
            pass
        return self.case(string)

    def _case(self, case_function):
        return type(self)(self.strings_class, self.key, case=case_function,
                          style=self.style, parent=self.parent)

    def lower(self):
        return self._case(str.lower)

    def upper(self):
        return self._case(str.upper)

    def capitalize(self):
        return self._case(str.capitalize)

    def title(self):
        return self._case(str.title)
