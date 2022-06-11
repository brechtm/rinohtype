Working with the stylesheet
===========================

To recap what we've built so far:

* a Sphinx project containing some content across multiple sections
* a PDF version of the output, using rinohtype's Sphinx builder, alongside
  Sphinx's built-in HTML rendering
* a local template configuration file, ``my-article.rtt``, that is invoked in
  ``conf.py``, and tells rinohtype to:

  * use the built-in ``article`` template
  * apply a stylesheet, ``allaboutme.rts``, that extends the built-in
    ``sphinx`` stylesheet

----


Applying styles to elements
---------------------------

You'll notice that each chapter of your document (*Plans*, *Skills*) starts on
an odd-numbered page. If necessary, rinohtype will add a page break (a blank
page, in effect) before each new chapter in order to force this.

In the :ref:`Sphinx style sheet` you'll find::

    [chapter]
    page_break=RIGHT

Just as ``emphasis`` and ``strong`` are examples of *elements* that it can
target, so is a ``chapter``. This style rule ensures that each ``chapter``
starts on a right-hand page.

Override this behaviour by adding::

    [chapter]
    page_break=LEFT

to your ``allaboutme.rts`` file, and rebuild. You'll now find that every
chapter starts on an even-numbered page instead.

But in a document this length it seems unnecessary to insert blank pages, so
change it to ``ANY`` - and now new chapters will start on a new page, on
either the left or right.

..  note:: Values in rinohtype stylesheets are case-insensitive.


Using variables in stylesheets
------------------------------

In the :ref:`Sphinx style sheet`, you'll see::

    [VARIABLES]
    mono_typeface=TeX Gyre Cursor
    serif_typeface=TeX Gyre Pagella
    sans_typeface=Tex Gyre Heros
    fallback_typeface=DejaVu Serif
    thin_black_stroke=0.5pt,#000
    blue=#20435c

    [default:Paragraph]
    typeface=$(serif_typeface)

in which the ``default:Paragraph`` element uses the ``serif_typeface`` variable defined above.

In your ``allaboutme.rts`` stylesheet, add a ``[VARIABLES]`` section with some definitions
of your own::

    [VARIABLES]
    mono_typeface=IBM Plex Mono
    serif_typeface=Joan
    sans_typeface=PT Sans
    blood-red=#6c1b206

These will override the previously-defined fonts. We have also defined a colour, ``blood-red``;
let's use it in the style rules for ``emphasis`` and ``strong`` (notice the syntax,
``$(variable-name)`` for using variables)::

    [emphasis]
    font_color=$(blood-red)

    [strong]
    font_color=$(blood-red)

``make rinoh`` again. If rinohtype cannot find the font files in the local project, it will
download them from `Google fonts <https://fonts.google.com>`_. You can try others (bear in mind
that font names *are* case-sensitive.)

..  warning::

    rinohtype is not able to parse all font properties, and you may run into an error with some
    typefaces.
