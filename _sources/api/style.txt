.. module:: rinoh.style

.. _style:

Style (:mod:`rinoh.style`)
==========================

.. autoclass:: Styled
    :members:
    :exclude-members: style_class

    .. autoattribute:: style_class
        :annotation:


.. autoclass:: Style
    :members:


Style Sheet
-----------

.. autoclass:: StyleSheet
    :members:

.. autoclass:: StyleSheetFile
    :members:

.. autoclass:: StyledMatcher
    :members:


.. _included_style_sheets:

Included Style Sheets
~~~~~~~~~~~~~~~~~~~~~

.. module:: rinoh.stylesheets

These style sheets are included with rinohtype:

.. autodata:: sphinx
    :annotation:

.. autodata:: sphinx_article
    :annotation:

.. autodata:: sphinx_base14
    :annotation:


Additional style sheets can be installed from PyPI. The installed style sheets
can be listed using :option:`rinoh --list-stylesheets`.


.. _default_matcher:

The Default Matcher
~~~~~~~~~~~~~~~~~~~

.. autodata:: rinoh.stylesheets.matcher
    :annotation:
