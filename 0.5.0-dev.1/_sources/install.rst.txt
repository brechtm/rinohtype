.. _installation:

Installation
============

rinohtype supports Python 3.3 and up. Use pip_ to install the latest version
of rinohtype and its dependencies::

    pip install rinohtype


If you plan on using rinohtype as an alternative to LaTeX, you will want to
install Sphinx_ as well::

    pip install Sphinx

See :ref:`sphinx_quickstart` in the :ref:`quickstart` guide on how to render
Sphinx documents with rinohtype.

.. _Sphinx: http://sphinx-doc.org


Dependencies
------------

For parsing reStructuredText and CommonMark documents, rinohtype depends on
docutils_ and recommonmark_ respectively. pip takes care of these requirements
automatically when you install rinohtype.

If you want to include images other than PDF, PNG or JPEG, you need to install
Pillow_ additionally.

.. _pip: https://pip.pypa.io
.. _docutils: http://docutils.sourceforge.net/index.html
.. _recommonmark: https://recommonmark.readthedocs.io
.. _Pillow: http://python-pillow.github.io
