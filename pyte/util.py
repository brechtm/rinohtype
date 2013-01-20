"""
Collection of miscellaneous classes, functions and decorators:

* :class:`Decorator`: Superclass for decorator classes of the decorator design
                      pattern
* :func:`all_subclasses`: Generator yielding all subclasses of `cls` recursively
* :func:`intersperse`: Generator inserting an element between every two elements
                       of a given iterable
* :class:`cached_property`: Caching property decorator
* :func:`timed`: Method decorator printing the time the method call took
"""


import time


__all__ = ['Decorator', 'all_subclasses', 'intersperse', 'cached_property',
           'timed']


# classes

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
        return object.__new__(cls, *args, **kwargs)

    def __init__(self, decoratee, *args, **kwargs):
        """The `decoratee` is stored in the decorator as the :attr:`_decoratee`
        attribute, where it is available for access by the decorator class."""
        self._decoratee = decoratee


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
