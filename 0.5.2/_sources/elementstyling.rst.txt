.. _styling:

Element Styling
===============

This section describes how styles defined in a style sheet are applied to
document elements. Understanding how this works will help you when designing
a custom style sheet.

rinohtype's style sheets are heavily inspired by CSS_, but add some additional
functionality. Similar to CSS, rinohtype makes use of so-called *selectors* to
select document elements in the *document tree* to style. Unlike CSS however,
these selectors are not directly specified in a style sheet. Instead, all
selectors are collected in a *matcher* where they are mapped to descriptive
labels for the selected elements. A *style sheet* assigns style properties to
these labels. Besides the usefulness of having these labels instead of the more
cryptic selectors, a matcher can be reused by multiple style sheets, avoiding
duplication.

.. note:: This section currently assumes some Python or general object-oriented
    programming knowledge. A future update will move Python-specific details
    to another section, making things more accessible for non-programmers.


.. _CSS: https://en.wikipedia.org/wiki/Cascading_Style_Sheets


Document Tree
-------------

A :class:`.Flowable` is a document element that is placed on a page. It is
usually a part of a document tree. Flowables at one level in a document tree
are rendered one below the other.

Here is schematic representation of an example document tree::

    |- Section
    |   |- Paragraph
    |   \- Paragraph
    \- Section
        |- Paragraph
        |- List
        |   |- ListItem
        |   |   |- Paragraph (item label; a number or bullet symbol)
        |   |   \- StaticGroupedFlowables (item body)
        |   |       \- Paragraph
        |   \- ListItem
        |       \- Paragraph
        |   |   \- StaticGroupedFlowables
        |   |       \- List
        |   |           |- ListItem
        |   |           |   \- ...
        |   |           \- ...
        \- Paragraph

This represents a document consisting of two sections. The first section
contains two paragraphs. The second section contains a paragraph followed by
a list and another paragraph. All of the elements in this tree are instances of
:class:`.Flowable` subclasses.

:class:`.Section` and :class:`List` are subclasses of
:class:`.GroupedFlowables`; they group a number of flowables. In the case of
:class:`.List`, these are always of the :class:`.ListItem` type. Each list item
contains an item number (ordered list) or a bullet symbol (unordered list) and
an item body. For simple lists, the item body is typically a single
:class:`.Paragraph`. The second list item contains a nested :class:`.List`.

A :class:`.Paragraph` does not have any :class:`.Flowable` children. It is
however the root node of a tree of *inline elements*. This is an example
paragraph in which several text styles are combined::

    Paragraph
     |- SingleStyledText('Text with ')
     |- MixedStyledText(style='emphasis')
     |   |- SingleStyledText('multiple ')
     |   \- MixedStyledText(style='strong')
     |       |- SingleStyledText('nested ')
     |       \- SingleStyledText('styles', style='small caps')
     \- SingleStyledText('.')

The visual representation of the words in this paragraph is determined by the
applied style sheet. Read more about how this works in the next section.

Besides :class:`.SingleStyledText` and :class:`.MixedStyledText` elements
(subclasses of :class:`.StyledText`), paragraphs can also contain
:class:`.InlineFlowable`\ s. Currently, the only inline flowable is
:class:`.InlineImage`.

The common superclass for flowable and inline elements is :class:`.Styled`,
which indicates that these elements can be styled using the style sheets.


Selectors
---------

Selectors in rinohtype select elements of a particular type. The *class* of a
document element serves as a selector for all instances of the class (and its
subclasses). The :class:`.Paragraph` class is a selector that matches all
paragraphs in the document, for example::

    Paragraph

As with `CSS selectors`_, elements can also be matched based on their context.
For example, the following matches any paragraph that is a direct child of a
list item or in other words, a list item label::

    ListItem / Paragraph

Python's :ref:`ellipsis <python:bltin-ellipsis-object>` can be used to match
any number of levels of elements in the document tree. The following selector
matches paragraphs at any level inside a table cell::

    TableCell / ... / Paragraph

To help avoid duplicating selector definitions, context selectors can reference
other selectors defined in the same :ref:`matcher <matchers>` using
:class:`SelectorByName`::

    SelectorByName('definition term') / ... / Paragraph

Selectors can select all instances of :class:`.Styled` subclasses. These
include :class:`.Flowable` and :class:`.StyledText`, but also
:class:`.TableSection`, :class:`.TableRow`, :class:`.Line` and :class:`.Shape`.
Elements of some of the latter classes only appear as children of other
flowables (such as :class:`.Table`).

Similar to a HTML element's *class* attribute, :class:`.Styled` elements can
have an optional *style* attribute which can be used when constructing a
selector. This one selects all styled text elements with the *emphasis* style,
for example::

    StyledText.like('emphasis')

The :meth:`.Styled.like` method can also match **arbitrary attributes** of
elements by passing them as keyword arguments. This can be used to do more
advanced things such as selecting the background objects on all odd rows of a
table, limited to the cells not spanning multiple rows::

    TableCell.like(row_index=slice(0, None, 2), rowspan=1) / TableCellBackground

The argument passed as *row_index* is a slice object that is used for extended
indexing\ [#slice]_. To make this work, :attr:`.TableCell.row_index` is an
object with a custom :meth:`__eq__` that allows comparison to a slice.

Rinohtype borrows CSS's concept of `specificity`_ to determine the "winning"
selector when multiple selectors match a given document element. Each part of
a selector adds to the specificity of a selector. Roughly stated, the more
specific selector will win. For example::

    ListItem / Paragraph                      # specificity (0, 0, 0, 0, 2)

wins over::

    Paragraph                                 # specificity (0, 0, 0, 0, 1)

since it matches two elements instead of just one.

Specificity is represented as a 5-tuple. The last four elements represent the
number of *location* (currently not used), *style*, *attribute* and *class*
matches. Here are some selectors along with their specificity::

    StyledText.like('emphasis')               # specificity (0, 0, 1, 0, 1)
    TableCell / ... / Paragraph               # specificity (0, 0, 0, 0, 2)
    TableCell.like(row_index=2, rowspan=1)    # specificity (0, 0, 0, 2, 1)

Specificity ordering is the same as tuple ordering, so (0, 0, 1, 0, 0) wins
over (0, 0, 0, 5, 0) and (0, 0, 0, 0, 3) for example. Only when the number of
style matches are equal, the attributes match count is compared and so on.

In practice, the class match count is dependent on the element being matched.
If the class of the element exactly matches the selector, the right-most
specificity value is increased by 2. If the element's class is a subclass of
the selector, it is only increased by 1.

The first element of the specificity tuple is the *priority* of the selector.
For most selectors, the priority will have the default value of 0. The priority
of a selector only needs to be set in some cases. For example, we want the
:class:`.CodeBlock` selector to match a :class:`.CodeBlock` instance. However,
because :class:`.CodeBlock` is a :class:`.Paragraph` subclass, another selector
with a higher specificity will also match it::

    CodeBlock                                 # specificity (0, 0, 0, 0, 2)
    DefinitionList / Definition / Paragraph   # specificity (0, 0, 0, 0, 3)

To make sure the :class:`.CodeBlock` selector wins, we increase the priority of
the :class:`.CodeBlock` selector by prepending it with a ``+`` sign::

    +CodeBlock                                # specificity (1, 0, 0, 0, 2)

In general, you can use multiple ``+`` or ``-`` signs to adjust the priority::

    ++CodeBlock                               # specificity (2, 0, 0, 0, 2)
    ---CodeBlock                              # specificity (-3, 0, 0, 0, 2)


.. _CSS selectors: https://en.wikipedia.org/wiki/Cascading_Style_Sheets#Selector
.. _specificity: https://en.wikipedia.org/wiki/Cascading_St174yle_Sheets#Specificity


.. _matchers:

Matchers
--------

At the most basic level, a :class:`.StyledMatcher` is a dictionary that maps
labels to selectors::

    matcher = StyledMatcher()
    ...
    matcher['emphasis'] = StyledText.like('emphasis')
    matcher['chapter'] = Section.like(level=1)
    matcher['list item number'] = ListItem / Paragraph
    matcher['nested line block'] = (GroupedFlowables.like('line block')
                                    / GroupedFlowables.like('line block'))
    ...

Rinohtype currently includes one matcher which defines labels for all common
elements in documents::

    from rinoh.stylesheets import matcher


Style Sheets
------------

A :class:`.StyleSheet` takes a :class:`.StyledMatcher` to provide element
labels to assign style properties to::

    styles = StyleSheet('IEEE', matcher=matcher)
    ...
    styles['strong'] = TextStyle(font_weight=BOLD)
    styles('emphasis', font_slant=ITALIC)
    styles('nested line block', margin_left=0.5*CM)
    ...

Each :class:`.Styled` has a :class:`.Style` class associated with it. For
:class:`.Paragraph`, this is :class:`.ParagraphStyle`. These style classes
determine which style attributes are accepted for the styled element. Because
the style class can automatically be determined from the selector, it is
possible to simply pass the style properties to the style sheet by calling the
:class:`.StyleSheet` instance as shown above.

Style sheets are usually loaded from a `.rts` file using
:class:`.StyleSheetFile`. An example style sheet file is shown in
:ref:`basics_stylesheets`.

A style sheet file contains a number of sections, denoted by a section title
enclosed in square brackets. There are two special sections:

- ``[STYLESHEET]`` describes global style sheet information (see
  :class:`.StyleSheetFile` for details)
- ``[VARIABLES]`` collects variables that can be referenced elsewhere in the
  style sheet

Other sections define the style for a document elements. The section titles
correspond to the labels associated with selectors in the
:class:`.StyledMatcher`. Each entry in a section sets a value for a style
attribute. The style for enumerated lists is defined like this, for example:

.. code-block:: ini

    [enumerated list]
    margin_left=8pt
    space_above=5pt
    space_below=5pt
    ordered=true
    flowable_spacing=5pt
    number_format=NUMBER
    label_suffix=')'

Since this is an enumerated list, *ordered* is set to ``true``. *number_format*
and *label_suffix* are set to produce list items labels of the style *1)*,
*2)*, .... Other entries control margins and spacing. See :class:`.ListStyle`
for the full list of accepted style attributes.

.. todo:: base stylesheets are specified by name ... entry points


Base Styles
~~~~~~~~~~~

It is possible to define styles which are not linked to a selector. These can
be useful to collect common attributes in a base style for a set of style
definitions. For example, the Sphinx style sheet defines the *header_footer*
style to serve as a base for the *header* and *footer* styles:

.. code-block:: ini

    [header_footer : Paragraph]
    base=default
    typeface=$(sans_typeface)
    font_size=10pt
    font_weight=BOLD
    indent_first=0pt
    tab_stops=50% CENTER, 100% RIGHT

    [header]
    base=header_footer
    padding_bottom=2pt
    border_bottom=$(thin_black_stroke)
    space_below=24pt

    [footer]
    base=header_footer
    padding_top=4pt
    border_top=$(thin_black_stroke)
    space_above=18pt

Because there is no selector associated with *header_footer*, the element type
needs to be specified manually. This is done by adding the name of the relevant
:class:`.Styled` subclass to the section name, using a colon (``:``) to
separate it from the style name, optionally surrounded by spaces.


Custom Selectors
~~~~~~~~~~~~~~~~

It is also possible to define new selectors directly in a style sheet file.
This allows making tweaks to an existing style sheet without having to create a
new :class:`.StyledMatcher`. However, this should be used sparingly. If a great
number of custom selectors are required, it is better to create a new
:class:`.StyledMatcher`

The syntax for specifying a selector for a style is similar to that when
constructing selectors in a Python source code (see `Matchers`_), but with a
number of important differences. A :class:`.Styled` subclass name followed by
parentheses represents a simple class selector (without context). Arguments to
be passed to :meth:`.Styled.like()` can be included within the parentheses.

.. code-block:: ini

    [special text : StyledText('special')]
    font_color=#FF00FF

    [accept button : InlineImage(filename='images/ok_button.png')]
    baseline=20%

Even if no arguments are passed to the class selector, it is important that the
class name is followed by parentheses. If the parentheses are omitted, the
selector is not registered with the matcher and the style can only be used as a
base style for other style definitions (see `Base Styles`_).

As in Python source code, context selectors are constructed using forward
slashes (``/``) and the ellipsis (``...``). Another selector can be referenced
in a context selector by enclosing its name in single or double quotes.

.. code-block:: ini

    [admonition title colon : Admonition / ... / StyledText('colon')]
    font_size=10pt

    [chapter title : LabeledFlowable('chapter title')]
    label_spacing=1cm
    align_baselines=false

    [chapter title number : 'chapter title' / Paragraph('number')]
    font_size=96pt
    text_align=right


Variables
~~~~~~~~~

Variables can be used for values that are used in multiple style definitions.
This example declares a number of typefaces to allow easily replacing the
fonts in a style sheet:

.. code-block:: ini

    [VARIABLES]
    mono_typeface=TeX Gyre Cursor
    serif_typeface=TeX Gyre Pagella
    sans_typeface=Tex Gyre Heros
    thin_black_stroke=0.5pt,#000
    blue=#20435c

It also defines the *thin_black_stroke* line style for use in table and frame
styles, and a specific color labelled *blue*. These variables can be referenced
in style definitions as follows:

.. code-block:: ini

    [code block]
    typeface=$(mono_typeface)
    font_size=9pt
    text_align=LEFT
    indent_first=0
    space_above=6pt
    space_below=4pt
    border=$(thin_black_stroke)
    padding_left=5pt
    padding_top=1pt
    padding_bottom=3pt


Another stylesheet can inherit (see below) from this one and easily replace
fonts in the document by overriding the variables.


Style Attribute Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~

The style system makes a distinction between text (inline) elements and
flowables with respect to how attribute values are resolved.

**Text elements** by default inherit the properties from their parent. Take for
example the *emphasis* style definition from the example above. The value for
style properties other than *font_slant* (which is defined in the *emphasis*
style itself) will be looked up in the style definition corresponding to the
parent element, which can be either another :class:`.StyledText` instance, or a
:class:`.Paragraph`. If the parent element is a :class:`.StyledText` that
neither defines the style attribute, lookup proceeds recursively, moving up in
the document tree.

For **flowables**, there is no fall-back to the parent's style by default.
A base style can be specified explicitly however. If a style attribute is not
present in a particular style definition, it is looked up in the base style.
This can help avoid duplication of style information and the resulting
maintenance difficulties. In the following example, the *unnumbered heading
level 1* style inherits all properties from *heading level 1*, overriding
only the *number_format* attribute:

.. code-block:: ini

    [heading level 1]
    typeface=$(sans_typeface)
    font_weight=BOLD
    font_size=16pt
    font_color=$(blue)
    line_spacing=SINGLE
    space_above=18pt
    space_below=12pt
    number_format=NUMBER
    label_suffix=' '

    [unnumbered heading level 1]
    base=heading level 1
    number_format=None

When a value for a particular style attribute is set nowhere in the style
definition lookup hierarchy, its default value is returned. The default values
for all style properties are defined in the class definition for each of the
:class:`.Style` subclasses.

For text elements, it is possible to override the default behavior of
falling back to the parent's style. Setting *base* to the label of a
:class:`.TextStyle` or :class:`.ParagraphStyle` prevents fallback to the parent
element's style.

For flowables, *base* can be set to ``PARENT_STYLE`` to enable fallback, but
this requires that the current element type is the same or a subclass of the
parent type, so it cannot be used for all styles.


Style Logs
----------

When rendering a document, rinohtype will create a :index:`style log`. It is
written to disk using the same base name as the output file, but with a
`.stylelog` extension. The information logged in the style log is invaluable
when debugging your style sheet. It tells you which style maps to each element
in the document.

The style log lists the document elements (as a tree) that have been rendered
to each page, and for each element all matching styles are listed together with
their specificity. No styles are listed when there aren't any selectors
matching an element and the default values are used. The winning style is
indicated with a ``>`` symbol. Styles that are not defined in the style sheet
or its base(s) are marked with an ``x``. If none of the styles are defined,
rinohtype falls back to using the default style.

Here is an example excerpt from a style log:

.. code-block:: text

    ...
      Paragraph('January 03, 2012', style='title page date')
           > (0,0,1,0,2) title page date
             (0,0,0,0,2) body
        SingleStyledText('January 03, 2012')
    ---------------------------------- page 3 ----------------------------------
    #### ChainedContainer('column1')
      DocumentTree()
        Section(id='structural-elements')             demo.txt:62 <section>
             > (0,0,0,1,2) chapter
          Heading('1 Structural Elements')            demo.txt:62 <title>
               > (0,0,0,1,2) heading level 1
                 (0,0,0,0,2) other heading levels
              MixedStyledText('1 Structural Elements')
                SingleStyledText('1')
                MixedStyledText(' ')
                  SingleStyledText(' ')
                SingleStyledText('Structural Elements')
          Paragraph('A paragraph.')                   demo.txt:64 <paragraph>
               > (0,0,0,0,2) body
            MixedStyledText('A paragraph.')
              SingleStyledText('A paragraph.')
          List(style='bulleted')                      demo.txt:66 <bullet_list>
               > (0,0,1,0,2) bulleted list
            ListItem()
                 x (0,0,1,0,4) bulleted list item
                 > fallback to default style
              ListItemLabel('•')
                   > (0,0,1,0,6) bulleted list item label
                     (0,0,0,0,2) list item label
                  MixedStyledText('•')
                    SingleStyledText('')
                    SingleStyledText('•')
              StaticGroupedFlowables()                demo.txt:66 <list_item>
                   > (0,0,0,0,3) list item body
    ...


.. [#slice] Indexing a list like this ``lst[slice(0, None, 2)]`` is equivalent
            to ``lst[0::2]``.
