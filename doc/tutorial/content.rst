Creating content
======================

Now is an appropriate time to add some content to work with.

The first page of the project is the ``index.rst`` file. You can replace the
entire contents of the file with the following (edit the text to your taste)::

    All about me
    ============

    Write a few paragraphs introducing yourself.

    Basic formatting in reStructuredText includes:

    * *emphasis*
    * **strong emphasis**
    * asterisks for list items

    Good things to include in your introduction would be a note about what you
    do and where you live.

Add a new file, ``plans.rst``, containing::

    My plans
    ========

    Say something about your plans.

    Short-term plans
    ----------------

    Perhaps you have some things that you intend to do in the near future.

    Long-term plans
    ---------------

    And perhaps you have some that will come later on.

The last thing to do is to add a table of contents to the ``index.rst`` file,
so it knows how to organise the content you have created. At the end of the
file, add::

    ..  toctree::
        :hidden:

        plans

You can add additional pages if you wish. For example, if you added
``my-family.rst``, you would need to add ``my-family`` below ``plans`` in the
``toctree`` (or indeed above it, if you wanted those sections in a different
order).

This isn't the place for a primer on Sphinx and rST, so you should look for
other resources if you need guidance on more ambitious formatting at this
stage.

Run ``make html`` and reload the ``index.html`` page to see the new content as
HTML; run ``make rinoh`` and re-open ``allaboutme.pdf`` to see the new version
of the PDF (if you're lucky, your PDF viewer will reload the changed file for
your automatically).
