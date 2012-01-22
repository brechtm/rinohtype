
import os
import time
from . import __file__ as pyte_file
from urllib.request import pathname2url
from urllib.parse import urljoin


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


def set_xml_catalog():
    if set_xml_catalog.done:
        return

    catalog_path = os.path.join(DATA_PATH, 'xml', 'catalog')
    catalog_url = urljoin('file:', pathname2url(catalog_path))
    try:
        xml_catalog_files = os.environ['XML_CATALOG_FILES'] + ' ' + catalog_url
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
