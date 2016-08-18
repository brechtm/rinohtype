Release History
---------------

Release 0.2.1 (2016-08-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* optionally limit the width of large images and make use of this to simulate
  the Sphinx LaTeX builder behavior (#46)
* reStructuredText/Sphinx: support for images with hyperlinks (#49)
* record the styled page numbers in the PDF as page labels (#41)
* unsupported Python versions: prevent installation where possible (sdist)
  or exit on import (wheel)
* support Python 3.6

Bugfixes:

* make StyleSheet objects picklable so the Sphinx builder's rinoh_stylesheet
  option can actually be used
* Fix #47: ClassNotFound exception in Literal_Block.lexer_getter()
* Fix #45: Images that don't fit are still placed on the page
* don't warn about duplicate style matches that resolve to the same style


Release 0.2.0 (2016-08-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Styling:

* generate a style log (show matching styles) to help style sheet development
* keep_with_next style attribute: prevent splitting two flowables across pages
* stylesheets can be loaded from files in INI format
* check the type of attributes passed to styles
* source code highlighting using Pygments
* table of contents entries can be styled more freely
* allow hiding the section numbers of table of contents entries
* allow for custom chapter titles
* selectors can now also select based on document part/section
* various small tweaks to selectors and matchers
* various fixes relating to style sheets

Templates:

* configurable standard document templates: article and book
* a proper infrastructure for creating custom document templates
* support for left/right page templates
* make the Article template more configurable
* pages now have background, content and header/footer layers
* support for generating an index
* make certain strings configurable (for localization, for example)

Frontends:

* Sphinx: interpret the LaTeX configuration variables if the corresponding
  rinohtype variable is not set
* Sphinx: roughly match the LaTeX output (document template and style sheet)
* added a CommonMark frontend based on recommonmark
* added basic ePUB and DocBook frontends
* XML frontends: fix whitespace handling
* frontends now return generators yielding flowables (more flexible)

Command-line Renderer (rinoh):

* allow specifying a template and style sheet
* automatically install typefaces used in the style sheet from PyPI

Fonts:

* typefaces are discovered/loaded by entry point
* more complete support for OpenType fonts
* fix support for the 14 base Type 1 fonts

Images:

* more versatile image sizing: absolute width/height & scaling
* allow specifying the baseline for inline images
* several fixes in the JPEG reader

Miscellaneous:

* reorganize the Container class hierarchy
* fixes in footnote handling
* drop Python 3.2 support (3.3, 3.4 and 3.5 are supported)


Release 0.1.3 (2015-08-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

* recover from the slow rendering speed caused by a bugfix in 0.1.2
  (thanks to optimized element matching in the style sheets)
* other improvements and bugfixes related to style sheets


Release 0.1.2 (2015-07-31)
~~~~~~~~~~~~~~~~~~~~~~~~~~

* much improved Sphinx support (we can now render the Sphinx documentation)
* more complete support for reStructuredText (docutils) elements
* various fixes related to footnote placement
* page break option when starting a new section
* fixes in handling of document sections and parts
* improvements to section/figure/table references
* native support for PNG and JPEG images
  (drops PIL/Pillow requirement, but adds PurePNG 0.1.1 requirement)
* new 'sphinx' stylesheet used by the Sphinx builder (~ Sphinx LaTeX style)
* restores Python 3.2 compatibility


Release 0.1.1 (2015-04-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~

First preview release
