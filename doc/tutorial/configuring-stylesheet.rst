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
