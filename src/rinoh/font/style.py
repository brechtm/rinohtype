# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.
from token import NUMBER

from ..attribute import OptionSet, OptionSetMeta


__all__ = ['FontWeight', 'FontSlant', 'FontWidth', 'FontVariant',
           'TextPosition']

from ..util import class_property


def hyphen_variants(value):
    yield value
    if '-' in value:
        yield value.replace('-', ' ')
        yield value.replace('-', '')


class ClassSetMeta(OptionSetMeta):
    def __new__(metacls, classname, bases, cls_dict):
        cls_dict['_lookup'] = {variant: klass
                               for klass, values in cls_dict['classes'].items()
                               for value in values
                               for variant in hyphen_variants(value)}
        return super().__new__(metacls, classname, bases, cls_dict)

    def __getattr__(cls, item):
        string = item.lower().replace('_', ' ')
        if item.isupper() and string in cls._lookup:
            return cls._lookup[string]
        raise AttributeError(item)


class ClassSet(OptionSet, metaclass=ClassSetMeta):
    classes = {}
    center = None
    offset = None
    range = None

    @classmethod
    def check_type(cls, value):
        if cls.range:
            min, max = cls.range
            return isinstance(value, int) and (min <= value <= max)
        else:
            return value in cls.classes.keys()

    @class_property
    def values(cls):
        return list(cls.classes.keys())

    @class_property
    def value_strings(cls):
        return [name for names in cls.classes.values() for name in names]

    @classmethod
    def from_tokens(cls, tokens, source):
        try:
            if tokens.next.type == NUMBER:
                option_string = next(tokens).string
                value = int(option_string)
                if not cls.check_type(value):
                    raise KeyError
            else:
                option_string = cls._value_from_tokens(tokens)
                value = cls._lookup[option_string.lower()]
        except KeyError:
            numeric_values = ('a value in the range [{}, {}]'
                              .format(*cls.range) if cls.range
                              else ', '.join(map(str, cls.classes)))
            raise ValueError("'{}' is not a valid {}. Must be one of: '{}'"
                             " or {}"
                             .format(option_string.strip(), cls.__name__,
                                     "', '".join(cls.value_strings),
                                     numeric_values))
        return value

    @classmethod
    def to_name(cls, klass):
        try:
            return cls.classes[klass][0]
        except KeyError:
            return str(klass)

    @classmethod
    def to_class(cls, value):
        return cls._lookup[value]

    @classmethod
    def nearest(cls, value, values):
        offset = (1 if value > cls.center else -1) * cls.offset
        _, val = sorted((abs((v + offset) - value), v) for v in values)[0]
        return val


class FontWeight(ClassSet):
    classes = {
        100: ['hairline', 'thin'],
        200: ['ultra-light', 'extra-light'],
        300: ['light'],
        400: ['regular', 'normal', 'book', 'roman'],
        500: ['medium'],
        600: ['semi-bold', 'demi-bold'],
        700: ['bold'],
        800: ['extra-bold', 'ultra-bold'],
        900: ['black', 'heavy'],
        950: ['extra-black', 'ultra-black'],
    }
    range = (0, 1000)
    center = 450
    offset = 1


class FontSlant(OptionSet):
    values = 'upright', 'oblique', 'italic'
    alternatives = dict(upright=('oblique', 'italic'),
                        oblique=('italic', 'upright'),
                        italic=('oblique', 'upright'))

    @classmethod
    def nearest(cls, value, values):
        if value not in values:
            value = next(v for v in cls.alternatives[value] if v in values)
        return value


class FontWidth(ClassSet):
    classes = {
        1: ['ultra-condensed'],
        2: ['extra-condensed'],
        3: ['condensed'],
        4: ['semi-condensed'],
        5: ['normal', 'medium'],
        6: ['semi-expanded'],
        7: ['expanded'],
        8: ['extra-expanded'],
        9: ['ultra-expanded'],
    }
    center = 5
    offset = -0.1


class FontVariant(OptionSet):
    values = 'normal', 'small capital', 'oldstyle figures'


class TextPosition(OptionSet):
    values = 'normal', 'superscript', 'subscript'


# for backward compatibility
REGULAR = FontWeight.REGULAR
MEDIUM = FontWeight.MEDIUM
BOLD = FontWeight.BOLD

UPRIGHT = FontSlant.UPRIGHT
OBLIQUE = FontSlant.OBLIQUE
ITALIC = FontSlant.ITALIC

CONDENSED = FontWidth.CONDENSED
NORMAL = FontWidth.NORMAL
EXPANDED = FontWidth.EXPANDED
