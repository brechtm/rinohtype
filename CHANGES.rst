Release History
---------------

.. note:: rinohtype uses `Semantic Versioning`__ for its releases. In summary,
    this means that each release gets a version number MAJOR.MINOR.PATCH. The
    MAJOR version number is increased when backwards-incompatible API changes
    are made. However, until we exit beta and reach version 1.0.0, anything may
    change at any time.

    With this in mind, to ease upgrading from a previous version, I try to
    explicitly list backward-incompatible changes in the *Changed* section for
    each release. Be sure to check these when upgrading.

    .. __: https://semver.org/


Release 0.5.5 (2024-07-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation changes:

* A showcase section was added to the manual to show examples of documents that
  can be produced by rinohtype.

New Features:

* Add support for Hungarian language (PR #425 by Pablo Alexis Domínguez Grau)
* Print alt text instead of error message when failing to render rst :image:
  directive (PR #410 by Timm638)
* Support for Spanish section and admonition titles (PR #400 by María Andrea
    Vignau)
* Enumerated list item labels now also respect the *number_separator* style
  property, enabling hierarchical list item labels (discussion #350).
* Admonitions now have a 'custom_title_text' property that can be used to
  style generic admonitions. For example, this style definition applies to
  ``.. admonition:: Fun Fact``::

      [fun fact admonition : Admonition(custom_title_text='Fun Fact')]
      base = admonition
      border_top = none
      border_bottom = none

Changed:

* handling of localized strings and user-defined strings has been reworked

  - built-in (localized) strings are now indicated by a ``@`` prefix, while
    user-defined strings have the ``$`` prefix
  - built-in strings can be overridden, and user-defined strings can be set in
    a template configuration file in the ``[STRINGS]`` section (with prefix!)

* "words" containing spaces (such as paths and URLs) can now be split before
  each forward slash for line wrapping (#188, #416)
* Support for Python 3.7 was dropped (end-of-life in June 2023)
* `MyST <https://github.com/executablebooks/MyST-Parser>`_ replaces
  `recommonmark <https://github.com/readthedocs/recommonmark>`_ for Markdown
  support (issues #265 and #370)
* The Article template has been overhauled. The title page and front matter
  parts have been removed and their contents are moved to the first content
  page. This makes the Article template more useful, since it was too similar
  to the Book template before.
* Template options whose purpose can also be fulfilled by setting the *hide*
  style property to ``true`` have been removed. The corresponding style
  definitions are:

  - ``TitlePageTemplate.show_date``: *title page date*
  - ``TitlePageTemplate.show_author``: *title page author*
  - ``Article.table_of_contents``: *table of contents section*

Fixed:

* Embedding of PDF images produces by Graphviz 10+
* Google Fonts downloading (https://github.com/google/fonts/issues/7481)
* Caption labels ("Figure", "Table", "Listing") were not localized
* Rendering of tables with no body (#420, PR #422 by th0mr)
* Hyphenation of the first word on a line (#188, #416)
* AttributeError: 'ZeroWidthSpace' object has no attribute 'hyphenate' (#415,
  PR #417 by Jack Whitham)
* Fix a Python 3.12 DeprecationWarning regarding utcfromtimestamp()
* Sphinx frontend: support the desc_sig_space document node (#414)
* Hyphenated word split across pages merges with the next word (#388)
* Compatibility with importlib-metadata 6.0.0 (#389)
* Document part templates were not retrieved recursively (#379 comment)
* Listing the installed fonts in a PDF: ``rinoh --list-fonts <filename>``
* Crash on rendering a heading with an index entry annotation (#369)
* Crash on encountering a fully-spanned table row (#369)
* Crash on rendering a figure caption with the default style (#368)
* Google Fonts fixes

  - Some fonts on Google Fonts have the 'otf' extension (instead of 'ttf');
    also collect these.
  - Look recursively for font files in a Google Fonts directory (e.g. Asap
    fonts are now stored in a deeper directory).


Release 0.5.4 (2022-06-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~

A `discussion board`_ has been set up where you can connect with other
rinohtype users and the developers!

.. _discussion board: https://github.com/brechtm/rinohtype/discussions

New Features:

* Support for sideways figures and tables; these are placed on a separate page,
  rotated 90 degrees. This is useful for figures/tables that do not fit within
  the page width. See the *float* style attribute.
* The GroupedFlowables *same_page* style property forces all of a
  GroupedFlowables' content to be placed on the same page (if possible).
* Support for OpenType fonts with non-BMP Unicode characters (PR #308 by James
  Robinson)
* Heading labels (numbers) can be styled separately by means of the 'heading
  level *X* label' selectors for each heading level *X*.
* Sphinx Graphviz extension (``sphinx.ext.graphviz``) support (PR #300 by
  Daniel Rapp)
* The StyledText *no_break_after* style property accepts a list of words after
  which no line break is allowed. The default is to use a list of words
  specific to the language configured for the template (articles, prepositions,
  conjunctions - only provided for English and Czech for now).
* Footnotes and citations can now optionally be rendered where they are located
  in the source document instead of as footnotes. This is controlled by the
  *location* style property for notes. (issue #269, PR #271 by Alex Fargus)
* The *before* and *after* style properties are now supported on paragraphs too
* The separator string between an inline admonition title and the admonition
  text is now specified in the style sheet (*after* property of the *admonition
  inline title* style), so it can be overridden (default: space character).
* Warn about targets in ``rinoh_targets`` that are not defined in
  ``rinoh_documents``.
* UpDownExpandingContainer: a container that symmetrically expands both upwards
  and downwards.
* Admonition: selectors for the first paragraph where the admonition title was
  prepended to (e.g. *note title paragraph*).
* Support interlaced PNG images (#274). Note that this can slow down rendering
  significantly for many/large interlaced images.
* rinoh now accepts the ``--versions`` argument, useful for bug reports

Changed:

* Support for Python 3.6 was dropped (end-of-life in December 2021)
* Provide a more informative exception message when Pillow cannot be imported.

Fixed:

* Fix cross-referencing of citations defined in the master Sphinx document
* ContainerOverflow when rendering (some) labeled flowables near the bottom of
  the page (issue #315)
* rinoh crashes with an unhandled exception when the template is not found
  (issue #291)
* ``rinoh --format`` option is broken (issue #284)
* Unhandled exception on loading some JPEG images (issue #319)
* Page breaks for sections following an empty section were not respected.
* Compatibility with Sphinx 4.4 on Python <3.10 (``AttributeError:
  'DynamicRinohDistribution' object has no attribute '_normalized_name'``)
* In some cases, footnotes referenced in a table were placed on the page
  preceding the footnote reference.
* Handle output (PDF, style log and cache) filenames containing a dot in the
  stem (the final dot and characters following it were interpreted as an
  extension and dropped)
* Compatibility with Sphinx 4.3 (crash on rendering object descriptions)
* Regression in handling of unsupported docutils nodes
* Crash due to floating point rounding error (PR #302 by Sam Hartman)
* Setting 'number_format' to *none* caused a crash; now it causes the caption
  label to be omitted.
* Handle citations and corresponding citation references that are not defined
  in the same source file.
* Fix error message for --stylesheet argument with relative path (issue #253,
  PR #266 by Alex Fargus)
* Descenders affect spacing between top border and content (issue #144)
* The table of contents (outlines) displayed in PDF readers show garbled text
  when section titles contain non-ASCII characters.
* Page templates with a page-filling background cause an infinite rendering
  loop when placing a footnote.
* Crash on loading PNGs containing an iTXt chunk (PR #275 by Alex Fargus)
* Line-wrapped section headings without hyphenation are missing from the page
  header.
* Sphinx frontend: inline text marked with the :menuselection: role is not
  styled (now mapped to the *menu cascade style*).
* Typos in code and documentation (PR #277 by Tim Gates, PR #281 by Filipe
  Tavares)
* Handle deprecation of importlib SelectableGroups dict interface (Python 3.10
  and importlib_metadata 3.6)
* Handle deprecation of distutils in Python 3.10 (use the packaging package)

Part of the work included in this release was kindly sponsored by `Lekis
<https://www.lekis.cz/>`_ and `Railnova <https://www.railnova.eu/>`_.


Release 0.5.3 (2021-06-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* Document part templates now accept a *page_number_prefix* (StyledText). For
  example, set ``page_number_prefix = '{SECTION_NUMBER(1)}-'`` to prefix the
  page number with the chapter number. You'll want to use this with the new
  page break options (see next item).
* The ``page_break`` style attribute now also accepts *left restart*, *right
  restart* and *any restart* values to restart page numbering
* The new *continue* page number format makes it more explicit when to not
  restart page numbering.
* Setting the *base* for a style to ``NEXT_STYLE`` proceeds to look up style
  attributes in the next matching style if they are undefined.
* The default matcher now defines the *table head cell background* style.
* Support True/OpenType fonts with 'Symbol' encoding (e.g. Web/Wingdings)
* If the *RINOH_NO_CACHE* environment variable is set, the references cache
  (.rtc file) won't be loaded nor saved. This is mostly useful for testing.

Changed:

* Smarter automatic sizing of table columns; don't needlessly pad columns whose
  contents don't require wrapping.

Fixed:

* Citation definitions are not output when using sphinx (#262, PR #268 by
  Alex Fargus)
* Setting the *base* for a style to ``PARENT_STYLE`` results in a crash.
* docutils image directive: crash when encountering a width/height containing a
  decimal point (#251 by Karel Frajtak)
* docutils inline images don't support width, height and scale options
* crash on using characters for page numbering (PDF backend)
* rinoh --install_resources: wrong section numbers when resources need to be
  installed
* The style of a heading is influenced by the style defined for the page header
* A heading is still displayed in the page header even if it doesn't fit on the
  page and thus moved to the next

Part of the work included in this release was kindly sponsored by `Joby
Aviation <https://www.jobyaviation.com>`_.


Release 0.5.2 (2021-02-24)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* If the *RINOH_SINGLE_PASS* environment variable is set, rendering will be
  stopped after a single pass. This speeds up iteration when tweaking style
  sheets or templates.
* Sphinx builder: the ``rinoh_targets`` configuration variable allows limiting
  the documents to a subset of those listed in ``rinoh_documents``.
* The 'number_format' style property can now also accept styled text strings
  which replace the auto-numbered label.
* Document elements (Styled objects) can more easily be matched based on their
  ID (or 'name' in docutils terms) by means of the *has_id* selector property.

Changed:

* docutils/Sphinx frontend: will default to referencing targets by number if
  possible, even if a custom label is explicitly set. This behaviour can be
  overridden in the style sheet by setting the *type* property of the
  *linked reference* style to 'custom' (see also issue #244).

Fixed:

* Sphinx style sheet: the object description is always rendered to the right
  of the signature, no matter how wide the signature is.
* Incorrect/useless warnings that popped up with release 0.5.1.

Part of the work included in this release was kindly sponsored by `Joby
Aviation <https://www.jobyaviation.com>`_.


Release 0.5.1 (2021-02-19)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* Paragraphs can now be numbered. rinohtype also allows for referencing them by
  number, but docutils/Sphinx doesn't readily offer the means express that. A
  workaround for this will be included in a future release.

Fixed:

* Fix issues with metadata (title, author) stored in the PDF Info dictionary
* Fix handling of no-break spaces (they were rendered using the fallback font)
* When a caption occurs in an unnumbered chapter, an exception aborts rendering
  (even when ``number_separator`` style attribute is set to ``None``)
* Handling of base template specified as string in a template configuration
* Table column widths entries now also accept fractions

Part of the work included in this release was kindly sponsored by `Joby
Aviation <https://www.jobyaviation.com>`_.


Release 0.5.0 (2021-02-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New Features:

* Google Fonts: if a specified typeface is not installed, rinohtype attempts
  to download the corresponding fonts from Google Fonts. Simply supply the font
  name as listed on https://fonts.google.com as a value for the ``typeface``
  style property.
* Table: in addition to fixed and relative-width columns, you can indicate
  columns to be automatically sized by specifying a value of 'auto' in the
  'column_widths' style parameter in your style sheet.
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
