
import os
import time
from urllib.request import pathname2url
from urllib.parse import urljoin


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


def set_xml_catalog():
    if set_xml_catalog.done:
        return

    catalog_path = os.path.join(DATA_PATH, 'xml', 'catalog')
    catalog_url = urljoin('file:', pathname2url(catalog_path))
    try:
        os.environ['XML_CATALOG_FILES'] += ' ' + catalog_url
    except KeyError:
        os.environ['XML_CATALOG_FILES'] = catalog_url
    set_xml_catalog.done = True

set_xml_catalog.done = False


def timed(f):
    """Decorator that times the function call."""
    def decorator(self, *args, **kwargs):
        name = self.__class__.__name__ + '.' + f.__name__
        start = time.clock()
        result = f(self, *args, **kwargs)
        print('{}: {:.4f} seconds'.format(name, time.clock() - start))
        return result
    return decorator


def recursive_subclasses(cls):
    """Generator that yields all subclasses of `cls` (recursive)"""
    for subcls in cls.__subclasses__():
        yield subcls
        for subsubcls in recursive_subclasses(subcls):
            yield subsubcls


class cached_property(property):
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
