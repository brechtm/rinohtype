
from distutils.core import setup
from Cython.Build import cythonize


setup (
    ext_modules=cythonize("rinoh/backend/pdf/show_glyphs.pyx")
)

