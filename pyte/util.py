"""Collection of miscellaneous utility functionality"""

import time


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


# method decorators

class cached_property(property):
    """Property decorator that additionally caches the return value of the
    decorated method. The value is stored as a data attribute of the object."""
    def __init__(self, function, *args, **kwargs):
        super().__init__(function, *args, **kwargs)
        self._function_name = function.__name__

    def __get__(self, obj, *args):
        cache_variable = '_cached_' + self._function_name
        try:
            return getattr(obj, cache_variable)
        except AttributeError:
            cache_value = super(cached_property, self).__get__(obj, *args)
            setattr(obj, cache_variable, cache_value)
            return cache_value


def timed(function):
    """Decorator timing the method call and printing the result to stdout."""
    def function_wrapper(self, *args, **kwargs):
        name = self.__class__.__name__ + '.' + function.__name__
        start = time.clock()
        result = function(self, *args, **kwargs)
        print('{}: {:.4f} seconds'.format(name, time.clock() - start))
        return result
    return function_wrapper
