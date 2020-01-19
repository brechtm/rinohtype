# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Collection of miscellaneous classes, functions and decorators:

* :class:`Decorator`: Superclass for decorator classes of the decorator design
                      pattern
* :func:`all_subclasses`: Generator yielding all subclasses of `cls` recursively
* :func:`intersperse`: Generator inserting an element between every two elements
                       of a given iterable
* :class:`cached_property`: Caching property decorator
* :class:`ReadAliasAttribute`: Descriptor creates a read-only alias for another
                               attribute
"""


import ntpath
import os
import posixpath

from collections import OrderedDict
from functools import wraps





# functions

def all_subclasses(cls):
    """Generator yielding all subclasses of `cls` recursively"""
    for subcls in cls.__subclasses__():
        yield subcls
        for subsubcls in all_subclasses(subcls):
            yield subsubcls


def intersperse(iterable, element):
    """Generator yielding all elements of `iterable`, but with `element`
    inserted between each two consecutive elements"""
    iterable = iter(iterable)
    yield next(iterable)
    while True:
        next_from_iterable = next(iterable)
        yield element
        yield next_from_iterable


class PeekIterator(object):
    """An _iterator that allows inspecting the next element"""

    def __init__(self, iterable):
        self.next = None
        self._iterator = iter(iterable)
        self._at_end = False
        self._advance()

    def _advance(self):
        result = self.next
        try:
            self.next = next(self._iterator)
        except StopIteration:
            self.next = None
            self._at_end = True
        return result

    def __iter__(self):
        return self

    def __next__(self):
        if self._at_end:
            raise StopIteration
        return self._advance()


def posix_path(path):
    return os.path.normpath(path).replace(ntpath.sep, posixpath.sep)


# function decorators

def consumer(function):
    """Decorator that makes a generator function automatically advance to its
    first yield point when initially called (PEP 342)."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        generator = function(*args, **kwargs)
        next(generator)
        return generator
    return wrapper


# method decorators

def cached(function):
    """Method decorator caching a method's returned values."""
    cache_variable = '_cached_' + function.__name__
    @wraps(function)
    def function_wrapper(obj, *args, **kwargs):
        # values are cached in a dict stored in the object
        try:
            cache = getattr(obj, cache_variable)
        except AttributeError:
            cache = {}
            setattr(obj, cache_variable, cache)
        args_kwargs = args + tuple(kwargs.values())
        try:
            return cache[args_kwargs]
        except KeyError:
            cache_value = function(obj, *args, **kwargs)
            cache[args_kwargs] = cache_value
            return cache_value
    return function_wrapper


class cached_property(property):
    """Property decorator that additionally caches the return value of the
    decorated getter method."""
    def __init__(self, function, *args, **kwargs):
        super().__init__(function, *args, **kwargs)
        self._cache_variable = '_cached_' + function.__name__

    def __get__(self, obj, *args):
        # the cached value is stored as an attribute of the object
        cache_variable = self._cache_variable
        try:
            return getattr(obj, cache_variable)
        except AttributeError:
            cache_value = super().__get__(obj, *args)
            setattr(obj, cache_variable, cache_value)
            return cache_value


def cached_generator(function):
    """Method decorator caching a generator's yielded items."""
    cache_variable = '_cached_' + function.__name__
    @wraps(function)
    def function_wrapper(obj, *args, **kwargs):
        # values are cached in a list stored in the object
        try:
            for item in getattr(obj, cache_variable):
                yield item
        except AttributeError:
            setattr(obj, cache_variable, [])
            cache = getattr(obj, cache_variable)
            for item in function(obj, *args, **kwargs):
                cache.append(item)
                yield item
    return function_wrapper



class class_property(object):
    """A read-only class property"""
    def __init__(self, function):
        self.function = function

    def __get__(self, obj, owner):
        return self.function(owner)




class Decorator(object):
    """Class simplifying the implementation of the decorater pattern, which
    allows for a sort of "run-time inheritance"."""

    def __new__(cls, decoratee, *args, **kwargs):
        """A decorator takes the object to be decorated as its first argument
        `decoratee`.

        Returns an object of a class with a name that is the concatenation of
        the class names of the decorator and decorated classes. It also inherits
        from these two classes."""
        cls = type(cls.__name__ + decoratee.__class__.__name__,
                   (cls, decoratee.__class__), decoratee.__dict__)
        return object.__new__(cls)

    def __init__(self, decoratee, *args, **kwargs):
        """The `decoratee` is stored in the decorator as the :attr:`_decoratee`
        attribute, where it is available for access by the decorator class."""
        self._decoratee = decoratee


# descriptors

# from "Caching and aliasing with descriptors (Python recipe)" by Denis Otkidach
class ReadAliasAttribute(object):
    """Descriptor creates a read-only alias for another attribute."""

    def __init__(self, name):
        self.name = name

    def __get__(self, inst, cls):
        if inst is None:
            return self
        return getattr(inst, self.name)


class NotImplementedAttribute(object):
    """Descriptor raising :class:`NotImplementedError` on attribute access"""
    def __get__(self, instance, owner):
        raise NotImplementedError('Attribute implementation is missing in '
                                  'subclass')


# from http://code.activestate.com/recipes/577426-auto-named-decriptors/
class NamedDescriptor(object):
    """Base class for descriptor's whose name will be derived from the attribute
    name the descriptor instance is assigned to. The `name` attribute will hold
    the desciptor name."""


class WithNamedDescriptors(type):
    """Set the names of the descriptors"""

    @classmethod
    def __prepare__(metacls, name, bases):
        return OrderedDict()  # keeps the order of member variables (PEP3115)

    def __new__(metacls, classname, bases, cls_dict):
        for name, attr in cls_dict.items():
            if isinstance(attr, NamedDescriptor):
                attr.name = name
        return super().__new__(metacls, classname, bases, cls_dict)


# context managers

class ContextManager(object):
    """Base for classes that can only be used as a context manager. Raises
    :class:`TypeError` if any other attributes besides :meth:`__enter__` and
    :meth:`__exit__` are accessed."""

    def __getattr__(self, item):
        raise TypeError('{} is a context manager'.format(type(self)))

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError


