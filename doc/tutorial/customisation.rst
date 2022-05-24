Basic customisation
====================

HTML
----

The next step is to manage *how* Sphinx builds the project. It's useful to use
an HTML theme whose output corresponds better to PDF rendering, so switch to
Furo; in ``conf.py``, edit the ``html_theme`` setting, to::

    html_theme = 'furo'

Rebuild the HTML to see the effect.


PDF
---

The PDF customisation is a little more complex. We need to do three things.

First, apply some rinoh configuration in ``conf.py``::

    rinoh_documents = [
        {
            "doc": "index",
            "target": "allaboutme",
            "template": "my-article.rtt"
        }
    ]

In brief, this means:

* build a document using the ``index`` file as the root
* name the output ``allaboutme``
* use the template configuration file in ``my-article.rtt``.

Next, create the ``my-article.rtt`` template configuration file that this will
use::

    [TEMPLATE_CONFIGURATION]
    name = My custom configuration
    template = article
    stylesheet = allaboutme.rts

``template = article`` refers to rinohtype's built-in ``article`` template (a
template is defined in Python).

``stylesheet = allaboutme.rts`` tells rinohtype to use a particular
stylesheet, which we need to create now as our final step::

    [STYLESHEET]
    name=My custom style sheet
    base=sphinx

    [emphasis]
    font_color=#f00

    [strong]
    font_color=#0f0

Here we told rinohtype to inherit from the built-in ``sphinx``
stylesheet, and apply RGB colours to *emphasis* and *strong* elements.

Rebuild the PDF to check that your changes have taken effect. As well as the
new colours, you should see that the new PDF is more compact than the previous
version, with fewer blank pages. This is because we're now using rinohtype's
``article`` template, rather than the default ``book`` - ``book`` is more
suited to much longer material, laid out as a traditional book.
