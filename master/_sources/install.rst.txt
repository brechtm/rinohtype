.. _installation:

Installation
============

rinohtype aims to support all stable Python 3 versions that have not reached
end-of-life_ status. Use pip_ to install the latest version of rinohtype and its
dependencies::

    pip install rinohtype

If your documents include maths, specify the *math* extra to install the
necessary additional requirements::

    pip install rinohtype[math]

If you plan on using rinohtype as an alternative to LaTeX, you will want to
install Sphinx_ as well::

    pip install Sphinx

See :ref:`sphinx_quickstart` in the :ref:`quickstart` guide on how to render
Sphinx documents with rinohtype.

.. _end-of-life: https://devguide.python.org/versions/#versions
.. _Sphinx: http://sphinx-doc.org


Dependencies
------------

For parsing reStructuredText and CommonMark documents, rinohtype depends on
docutils_ and myst-parser_ respectively. pip takes care of these requirements
automatically when you install rinohtype.

If you want to include images other than PDF, PNG or JPEG, you need to install
Pillow_ additionally.

.. _pip: https://pip.pypa.io
.. _docutils: http://docutils.sourceforge.net/index.html
.. _myst-parser: https://myst-parser.readthedocs.io
.. _Pillow: http://python-pillow.github.io
