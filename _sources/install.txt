.. _installation:

Installation
============

RinohType supports Python 3.2 and up. Depending on demand, it might be
back-ported to Python 2.7, however\ [1]_.

Use pip_ to install the latest version of RinohType and its dependencies::

    pip install rinohtype


If you plan on using RinohType as an alternative to LaTeX, you will want to
install Sphinx_ as well::

    pip install Sphinx

See :ref:`sphinx_quickstart` in the :ref:`quickstart` guide on how to render
Sphinx documents with RinohType.

.. _Sphinx: http://sphinx-doc.org


Dependencies
------------

For parsing reStructuredText documents RinohType depends on docutils_. For
parsing PNG images the pure-Python PurePNG_ package is required. pip takes care
of these requirements automatically when you install RinohType.

If you want to include images other than PDF, PNG or JPEG, you will need to
install Pillow_ additionally.

.. _docutils: http://docutils.sourceforge.net/index.html
.. _pip: https://pip.pypa.io
.. _PurePNG: http://purepng.readthedocs.org
.. _Pillow: http://python-pillow.github.io


.. [1] Be sure to contact us if you are interested in running RinohType on
       Python 2.7.
