
from distutils.core import setup
from Cython.Build import cythonize
import Cython.Compiler.Options

Cython.Compiler.Options.annotate = True

setup (
    ext_modules=cythonize(["rinoh/font/glyphmetrics.pyx",
                           "rinoh/backend/pdf/show_glyphs.pyx",
                           "rinoh/cparagraph.pyx"])
)
