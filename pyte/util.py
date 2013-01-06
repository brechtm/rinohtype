"""
Collection of miscellaneous utility functions and decorators:

* `all_subclasses`: Generator yielding all subclasses of `cls` recursively
* `intersperse`: Generator inserting an element between every two elements of
                 a given iterable
* `cached_property`: Caching property decorator
* `timed`: Method decorator printing the time the method call took
"""

import time


__all__ = ['all_subclasses', 'intersperse', 'cached_property', 'timed']


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
    decorated getter method"""
    def __init__(self, function, *args, **kwargs):
        super().__init__(function, *args, **kwargs)
        self._function_name = function.__name__

    def __get__(self, obj, *args):
        #  the cached value is stored as an attribute of the object
        cache_variable = '_cached_' + self._function_name
        try:
            return getattr(obj, cache_variable)
        except AttributeError:
            cache_value = super().__get__(obj, *args)
            setattr(obj, cache_variable, cache_value)
            return cache_value


def timed(function):
    """Decorator timing the method call and printing the result to `stdout`"""
    def function_wrapper(self, *args, **kwargs):
        """Wrapper function printing the time taken by the call to `function`"""
        name = self.__class__.__name__ + '.' + function.__name__
        start = time.clock()
        result = function(self, *args, **kwargs)
        print('{}: {:.4f} seconds'.format(name, time.clock() - start))
        return result
    return function_wrapper
