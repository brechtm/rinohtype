Release History
---------------

Release 0.5.0 (2021-02-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* Google Fonts: if a specified typeface is not installed, rinohtype attempts
  to download the corresponding fonts from Google Fonts. Simply supply the font
  name as listed on https://fonts.google.com as a value for the ``typeface``
  style property.
* Table: in addition to fixed and relative-width columns, you can indicate
  columns to be automatically sized by specifying a value of 'auto' in the
  'column_widths' style parameter in yout style sheet.
* docutils frontend: support the ``:align:`` option to table directives, which
  will override the alignment set for the table in the style sheet.
* The starting number of enumerated lists in reStructuredText is respected.
* Table column widths can be specified in the style sheet, which take effect
  when these haven't been specified in the source document.
* Document elements now store where they have been defined (document tree,
  style sheet file or template configuration file); when you specify relative
  paths (e.g. for images), they are interpreted relative to the location of
  their source. This should make things more intuitive.
* The ``page_break`` style attribute is no longer reserved for sections; a
  page break can be forced before any flowable.
* Enumerated list items with a hidden label ('hide' style attribute) are no
  longer counted in the numbering.
* Templates and typefaces can be registered by name at runtime. This makes them
  referencable from template configuration and style sheet files. For example,
  custom templates/typefaces can be imported in a Sphinx project's `conf.py`
  (to be documented).
* It's now possible to add arbitrary reStructuredText content to the front/back
  matter or  elsewhere by adding a ``.. container::`` with the 'out-of-line'
  class and a ``:name:`` to reference it by in the document template
  configuration, e.g. in the list of front matter flowables (to be documented).
* Selectors in style sheet files (.rts) now support boolean and 'None' values.
  For example, you can select StaticGroupedFlowables based on whether they have
  any children or not: e.g ``TableCell(empty=true)`` selects empty table cells.
* The document's title and author are now stored in the PDF metadata.
* "0" is now accepted as a valid value for Dimension-type attributes in style
  sheets and template configurations.

Changed:

* Rendering speed was more than doubled (caching)! (PR #197 by Alex Fargus)
* Sphinx frontend: ``rinoh_documents`` now takes a list of dictionaries, one
  for each PDF document to be built. This allows selecting e.g. the template
  and logo on a per-document level. Support for ``rinoh_template``,
  ``rinoh_stylesheet``, ``rinoh_paper_size``, ``rinoh_domain_indices`` and
  ``rinoh_logo`` was removed. Fallback to ``latex_documents`` is retained.
  (PR #182, #192, #195, #208 and #216 by Alex Fargus)
* The default stylesheet ('Sphinx') now prevents captions from being separated
  from their image/table/code block (across pages).
* Font weights and widths are now internally represented by integer classes.
  In addition to integer values, string values are still accepted (mapped to
  classes).
* OpenTypeFont now determines the font weight, slant and width from the file.
  For backward compatibility, it still accepts these as arguments on
  instantiation but warns when they don't match the values stored in the font.

Fixed:

* Table column width determination was overhauled. Now fixed-width tables are
  supported and automatic-width columns should be handled better.
* The 'nested bulleted/enumerated list' selectors were broken; their
  corresponding styles were never applied
* Items inside a table cannot be referenced (issue #174)
* Sphinx frontend: fix handling of relative image paths in .rst files inside
  a directory in the Sphinx project root
* rinoh: fix --install-resources (broken since PyPI disabled XMLRPC searches)
* GroupedLabeledFlowables: respect label_min_width and fix a crash with respect
  to space_below handling
* Duplicate rendering of content in columns; if content was too small to fill
  the first column, it was rendered again in subsequent columns.
* Crash on encountering a style for which no selector is defined.

Part of the work included in this release was kindly sponsored by `Joby
Aviation <https://www.jobyaviation.com>`_.


Release 0.4.2 (2020-07-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* before/after style attributes for StyledText (issue #158)
* docutils/Sphinx frontend: don't abort on encountering math/math_block, output
  the (LaTeX) math markup instead, along with printing a warning.
* docutils frontend: raw inline text (with ``:format: 'rinoh'``) is parsed as
  styled text

Fixed:

* crash when the 'contents' topic has multiple IDs (issue #173)
* loading of the references cache (issue #170)
* some issues with space_below handling


Release 0.4.1 (2020-07-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* UserStrings: arbitrary user-defined strings that can be defined in the
  template configuration or as a substitution definition in reStructuredText
* strings in a StringCollection can now be styled text
* Sphinx frontend: use the ``today`` and ``today_fmt`` configuration variables
  for the date on the title page
* Sphinx frontend: allow extensions access to the builder object (issue #155)
* rinoh: ``--output`` writes the output PDF to a specified location

Fixed:

* Regression in handling images that don't fit on the current page (issue #153)
* Fix crash when rendering local table of contents (issue #160)
* Sphinx frontend: support code-block/literalinclude with caption (issue #128)
* rinoh: variables set in a template configuration file are sometimes ignored
  (issue #164)
* Crash when using a font that contains unsupported lookups (issue #141)


Release 0.4.0 (2020-03-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* automatically generated lists of figures and tables
* paragraphs now provide default tab stops (proportional to font size) for
  indentation
* stylesheet (.rts) and template configuration (.rtt) files now support
  specifying inline and background images (#107 and #108); to be documented
* it is now possible to specify selector priority (+-) in style sheets
* Sphinx frontend: the rinoh builder can be discovered by entry point
  (no more need to add 'rinoh.frontend.sphinx' to the list of extensions)
* rinoh: set a return code of 1 when one or more referenced images could not be
  found (issue #104)
* rinoh: introduce the ``--install-resources`` option to control the automatic
  installation of resources from PyPI
* German locale (contributed by Michael Kaiser)
* Polish locale (contributed by Mariusz Jamro)

Changed:

* Python 3.3 & 3.4 are no longer supported since they have reached end-of-life
* remove the dependency on purepng by embedding its png.py
* limit the width of images to the available width by default
* XML frontend: special case mixed content nodes
* fixes in the design of stylesheet/template code

Fixed:

* various regressions (PR #142 by Norman Lorrain)
* fix issues with variables defined in a base style sheet/template config
* various footnote rendering issues
* border width is also taken into account for flowables that are continued on a
  new page (#127)
* Sphinx: handle case when source_suffix is a list (PR #110 by Nick Barrett)
* incompatibility with Sphinx 1.6.1+ (latex_paper_size)
* docutils: crash when a footnote is defined in an admonition (issue #95)
* docutils: crash on encountering a raw text role (issue #99)
* docutils: 'decoration' node (header/footer) is not yet supported (issue #112)
* crash when a table cell contains (only) an image
* colours of PNG images with gamma (gAMA chunk) set are incorrect (#102)
* Sphinx: image paths with wildcard extension are not supported (#119)
* GroupedFlowables: space_below should only be considered at the end
* adapt to PEP 479 (Change StopIteration handling inside generators), the
  default in Python 3.7 (issue #133)
* fix compatibility with Python 3.6.7 and 3.7.1 (tokenizer changes)
* fix crash caused by Python 3.8's changes to int.__str__


Release 0.3.1 (2016-12-19)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* rinoh is now also available as a stand-alone application for both Windows
  (installer) and macOS (app); they include an embedded CPython installation
* index terms can be StyledText now (in addition to str)
* the 'document author' metadata entry can now be displayed using a Field
* Sphinx frontend: support the 'desc_signature_line' node (new in Sphinx 1.5)
* rinoh --docs: open the online documentation in the default browser

Changed:

* more closely mimic the Sphinx LaTeX builder's title page (issue #60)
* there is no default for PageTemplate.chapter_title_flowables anymore since
  they are specific to the document template

Fixed:

* handle StyledText metadata (such as document title)
* Sphinx frontend: support the 'autosummary_toc' node
* DummyFlowable now sticks to the flowable following it (keep_with_next), so
  that (1) it does not break this behavior of Heading preceding it, and
  (2) IndexTargets do not get separated from the following flowable
* bug in LabeledFlowable that broke keep_with_next behavior
* the descender size of the last flowable in a GroupedFlowables with
  keep_with_next=True was getting lost
* GroupedFlowables should not mark the page non-empty; this caused empty pages
  before the first chapter if it is preceded by grouped DummyFlowables


Release 0.3.0 (2016-11-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* support localization of standard document strings (en, fr, it, nl) (#53)
* localized strings can be overridden in the document template configuration
* make use of a fallback typeface when a glyph is not available (#55)
  (the 'fallback' style in the Sphinx stylesheet sets the fallback typeface)
* template configuration (INI) files: specify which document parts to include,
  configure document part and page templates, customize localized strings, ...
* support specifying more complex selectors directly in a style sheet file
* (figure and table) captions support hierarchical numbering (see CaptionStyle)
* make the frontends independent of the current working directory
* reStructuredText: support the table :widths: option (upcoming docutils 0.13)
* Sphinx frontend: provide styles for Sphinx's inline markup roles
* rinoh (command line renderer):

  - support template configuration files
  - support file formats for which a frontend is installed (see --list-formats)
  - accept options to configure the frontend (see --list-options)
  - option to list the installed fonts (on the command line or in a PDF file)

* show the current page number as part of the rendering progress indicator
* Book template: support for setting a cover page
* frontends: raise a more descriptive exception when a document tree node is
  not mapped
* validate the default value passed to an Attribute
* preliminary support for writing a style sheet to an INI file, listing default
  values for non-specified attributes (#23)

Changed:

* rinoh: the output PDF is now placed in the current directory, not in the same
  directory as the input file
* Sphinx builder configuration: replace the ``rinoh_document_template`` and
  ``rinoh_template_configuration`` options with ``rinoh_template``
* if no base is given for a style, style attribute lookup proceeds to look in
  the style of the same name in the base style sheet (#66)
* DEFAULT_STYLE can be used as a base style to prevent style attribute lookup
  in the style of the same name in the base style sheet
* rename FieldList to DefinitionList and use it to replace uses (docutils and
  Sphinx frontends) of the old DefinitionList (#54)
* the new DefinitionList (FieldList) can be styled like the old DefinitionList
  by setting max_label_width to None, 0 or a 0-valued Dimension
* figures are now non-floating by default (float placement needs more work)
* hide the index chapter when there are no index entries (#51)
* style sheets: use the default matcher if none is specified
* Sphinx style sheet: copy the admonition style from the Sphinx LaTeX builder
* Sphinx style sheet: keep the admonition title together with the body
* Sphinx style sheet: color linked references as in the LaTeX output (#62)
* Sphinx style sheet: disable hyphenation/ligatures for literal strong text
* no more DocumentSection; a document now consists of parts (containing pages)
* template configuration:

  - refer to document part templates by name so that they can be replaced
  - the list of document parts can be changed in the template configuration
  - document parts take the 'end_at_page' option (left, right, or any)
  - find (left/right) page templates via the document part name they belong to
  - fall back to <doc_part>_page when the right or left template is not found
  - each template configuration requires a name

* DocumentTree: make the ``source_file`` argument optional
* don't abort when the document section hierarchy is missing levels (#67)
* use the PDF backend by default (no need to specify it)
* store the unit with Dimension instances (better printing)
* rename the `float` module to `image`

Fixed:

* improve compatibility with Windows: Windows path names and file encoding
* crash if a StyledText is passed to HeadingStyle.number_separator
* GroupedLabeledFlowables label width could be unnecessarily wide
* fix and improve automatic table column sizing
* Figures can now be referenced using the 'reference' format ("Figure 1.2")
* HorizontallyAlignedFlowable: make more robust
* make document elements referenceable by secondary IDs
* reStructuredText: only the first classifier for a definition term was shown
* Sphinx frontend: support the 'centered' directive
* Sphinx frontend: basic support for the 'hlist' directive
* Sphinx frontend: handle :abbr: without explanation
* Sphinx frontend: support nested inline nodes (guilabel & samp roles)
* PDF backend: fix writing of Type 1 fonts from a parsed PDF file
* PDF reader: handle multi-page PDFs (#71)
* PDF reader: fix parsing of XRef streams
* PDF reader: fix writing of parsed files


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
