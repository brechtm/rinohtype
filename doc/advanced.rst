.. _advanced:

Advanced Topics
===============

This sections serves as a reference for various building blocks making up
RinohType. The information presented here is useful for those who want to learn
how document templates and styling work in RinohType, which is helpful when
creating custom style sheets and document templates.


Flowables and Inline Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: rinoh.flowable

A :class:`Flowable` is a document element that is placed on a page. It is
usually a part of a document tree. Flowables at one level in a document tree are
rendered one below the other.

Here is schematic representation of an example document tree::

    |- Section
    |   |- Paragraph
    |   \- Paragraph
    \- Section
        |- Paragraph
        |- List
        |   |- ListItem
        |   |   |- Paragraph (item number or bullet)
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
:class:`Flowable` subclasses.

:class:`Section` and :class:`List` are subclasses of :class:`GroupedFlowables`;
they group a number of other flowables. In the case of :class:`List`, these are
always of the :class:`ListItem` type. Each list item contains an item number
(ordered list) or a bullet symbol (unordered list) and an item body. For simple
lists, the item body is typically a single :class:`Paragraph`. The second list
item contains a nested :class:`List`.

A :class:`Paragraph` does not have any :class:`Flowable` children. It is however
the root node of a tree of inline elements. This is an example paragraph in
which several text styles are combined::

    Paragraph
     |- SingleStyledText('Text with ')
     |- MixedStyledText(style='emphasis')
     |   |- SingleStyledText('multiple ')
     |   \- MixedStyledText(style='strong')
     |       |- SingleStyledText('nested ')
     |       \- SingleStyledText('styles', style='small caps')
     \- SingleStyledText('.')

The eventual style of the words in this paragraph is determined by the applied
style sheet. Read more about this in the next section.

Besides :class:`SingleStyledText` and :class:`MixedStyledText` elements
(subclasses of :class:`StyledText`), paragraphs can also contain
:class:`InlineFlowable`\ s. Currently, the only inline flowable is
:class:`InlineImage`.

The common superclass for flowable and inline elements is :class:`Styled`, which
indicates that these elements can be styled using the style sheets discussed in
the next section.


Style Sheets
~~~~~~~~~~~~

RinohType's style sheets are heavily inspired by CSS_, but add some
functionality that CSS lacks. Similar to CSS, RinohType makes use of so-called
*selectors* to select document elements (flowables or inline elements) to style.

Unlike CSS however, these selectors are not directly specified in a style sheet.
Instead, all selectors are collected in a *matcher* where they are mapped to
descriptive labels for the selected elements. The actual *style sheets* assign
style properties to these labels. Besides the usefulness of having these labels
instead of the more cryptic selectors, a matcher can be reused by multiple style
sheets, avoiding duplication.

.. _CSS: https://en.wikipedia.org/wiki/Cascading_Style_Sheets


Selectors
.........

Selectors in RinohType always select elements of a particular type. The
**class** of a document element is also a selector for all instances of the
class (and its subclasses). This selector matches all paragraphs in the
document, for example::

    Paragraph

As with `CSS selectors`_, elements can also be matched based on their context.
For example, the following matches any paragraph that is a direct child of a
list item (the list item number or symbol)::

    ListItem / Paragraph

`Python's ellipsis`_ can be used to match any number of levels of elements in
the document tree. The following selector matches any paragraph element at any
level inside a table cell::

    TableCell / ... / Paragraph

Selectors can select all instances of :class:`Styled` subclasses. These include
:class:`Flowable` and :class:`StyledText`, but also :class:`TableSection`,
:class:`TableRow`, :class:`Line` and :class:`Shape`. Elements of the latter
classes are children of certain flowables (such as table).

Similar to HTML/CSS's *class* attribute, :class:`Styled` elements can have a
**style** attribute which can be specified when constructing a selector. This
one selects all styled text elements with the *emphasis* style, for example::

    StyledText.like('emphasis')

The :meth:`like` method can also match **arbitrary attributes** of elements.
This can be used to do more advanced things such as selecting the background
objects on all odd rows of a table, limited to the cells not spanning multiple
rows::

    TableCell.like(row_index=slice(0, None, 2), rowspan=1) / TableCellBackground

The argument passed as *row_index* is slice object that is used for extended
indexing. Indexing a list ``lst[slice(0, None, 2)]`` is equivalent to
``lst[0::2]``.

RinohType borrows CSS's concept of `specificity`_ to determine the "winning"
selector when multiple selectors match a given document element. Roughly stated,
the more specific selector will win. For example::

    ListItem / Paragraph                      # specificity (0, 0, 2)

wins over::

    Paragraph                                 # specificity (0, 0, 1)

since it matches two elements instead of just one.

Specificity is represented as a 3-tuple. The three elements represent the number
of style, attributes and class matches. Here are some selectors along with their
specificity::

    StyledText.like('emphasis')               # specificity (1, 0, 1)
    TableCell / ... / Paragraph               # specificity (0, 0, 2)
    TableCell.like(row_index=2, rowspan=1)    # specificity (0, 1, 1)

Specificity ordering is the same as tuple ordering, so (1, 0, 0) wins over
(0, 5, 0) and (0, 0, 3) for example. Only when the number of style matches are
equal the attributes match count is compared, and so on.

.. _CSS selectors: https://en.wikipedia.org/wiki/Cascading_Style_Sheets#Selector
.. _Python's ellipsis: https://docs.python.org/3.5/library/constants.html#Ellipsis
.. _specificity: https://en.wikipedia.org/wiki/Cascading_Style_Sheets#Specificity


Matchers
........

At the most basic level, a :class:`StyledMatcher` is a dictionary that maps
descriptions to selectors::

    matcher = StyledMatcher()
    ...
    matcher['emphasis'] = StyledText.like('emphasis')
    matcher['chapter'] = Section.like(level=1)
    matcher['list item number'] = ListItem / Paragraph
    matcher['nested line block'] = (GroupedFlowables.like('line block')
                                    / GroupedFlowables.like('line block'))
    ...


Style Sheets
............

A :class:`StyleSheet` takes a :class:`StyledMatcher` to provide element labels
to assign style properties to::

    styles = StyleSheet('IEEE', matcher=matcher)
    ...
    styles('emphasis', font_slant=ITALIC)
    styles('nested line block', margin_left=0.5*CM)
    ...

Each :class:`Styled` has a :class:`Style` class associated with it. For
:class:`Paragraph`, this is :class:`ParagraphStyle`. These style classes
determine which style attributes are accepted for the styled element. The style
class is automatically determined from the selector, so it is possible to simply
pass the style properties to the style sheet.


Variables
,,,,,,,,,

Variables can be used for values that are used in multiple style definitions.
This example declares a variable `font_family` to allow easily changing the
fonts in a style sheet::

    from rinoh.font import TypeFamily

    from rinohlib.fonts.texgyre.pagella import typeface as palatino
    from rinohlib.fonts.texgyre.cursor import typeface as courier
    from rinohlib.fonts.texgyre.heros import typeface as helvetica

    styles.variables['font_family'] = TypeFamily(serif=times,
                                                 sans=helvetica,
                                                 mono=courier)
    ...
    styles('monospaced',
           typeface=Var('font_family').mono,
           font_size=9*PT,
           hyphenate=False,
           ligatures=False)
    ...

Another stylesheet can inherit (see below) from this one and easily replace all
fonts in the document by overriding the ``font_family`` variable.

Style Property Resolution
,,,,,,,,,,,,,,,,,,,,,,,,,

The style system makes a distinction between text (inline) elements and
flowables with respect to how property values are resolved.

**Text elements** by default inherit the properties from their parent. Take for
example the ``emphasis`` style definition from the example above. The value for
style properties other than ``font_slant`` (which is defined in the ``emphasis``
style itself) will be looked up in the style definition corresponding to the
parent element. That can be another :class:`StyledText` instance, or a
:class:`Paragraph`. If that style definition neither defines the style property,
the lookup proceeds recursively, moving up in the document tree.

For **flowables**, there is no fall-back to the parent's style by default.
A base style can be explicitly specified however. If a style property is not
defined in a particular style definition, it is looked up in the base style.

This can also help avoid duplication of style information and the resulting
maintenance difficulties. In the following example, the ``unnumbered heading
level 1`` style inherits all properties from ``heading level 1``, overriding
only the ``number_format`` property::

    styles('heading level 1',
           typeface=Var('ieee_family').serif,
           font_weight=REGULAR,
           font_size=10*PT,
           small_caps=True,
           justify=CENTER,
           line_spacing=FixedSpacing(12*PT),
           space_above=18*PT,
           space_below=6*PT,
           number_format=ROMAN_UC,
           label_suffix='.' + FixedWidthSpace())

    styles('unnumbered heading level 1',
           base='heading level 1',
           number_format=None)

When a value for a particular style property is set nowhere in the style
definition lookup hierarchy its default value is returned. The default values
for all style properties are defined in the class definition of the
:class:`Style` subclasses.

For both text elements and flowables, it is possible to override the default
behavior of falling back to the parent's style or not. For :class:`TextStyle`
styles, setting ``base`` to ``None`` or another :class:`TextStyle` prevents
fallback to the parent element's style. For flowables, ``base`` can be set to
``PARENT_STYLE`` to enable fallback, but this requires that the current
element type is the same or a subclass of the parent type, so it is not
recommended.