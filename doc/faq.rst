.. _faq:

Frequenty Asked Questions
=========================

This is a list of commonly encountered problems and solutions to them.


PDFs produced by rinohtype contain mostly empty pages. What's up?
    Old versions of some PDF viewers do not support the way rinohtype embeds
    fonts in a PDF (see `issue 2`_). PDF viewers that are known to be affected
    are:

    - pre-37.0 Firefox's built-in PDF viewer (pdf.js)
    - pre-0.41 poppler_-based applications such as Evince

    .. _issue 2: https://github.com/brechtm/rinohtype/issues/2
    .. _poppler: http://poppler.freedesktop.org


Installing rinohtype using pip fails with *rinohtype requires Python 3.3 or higher*
    rinohtype only works on Python 3.3 or higher. Make sure the `pip` you are
    using is one from a Python 3.3+ installation using ``pip --version``. On
    some operating systems, you may need to use ``pip3``.
