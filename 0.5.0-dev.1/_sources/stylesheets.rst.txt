.. _style_sheets:

Style Sheets
============

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

Default Matcher
~~~~~~~~~~~~~~~

The default matcher provides the selectors for the styles used in the standard
style sheets.

.. autodata:: rinoh.stylesheets.matcher
    :annotation:

Element Style Classes
~~~~~~~~~~~~~~~~~~~~~

These are the style classes corresponding to each type of document element. For
each style class, the supported style attributes are listed along with the
values that can be assigned to them in a style sheet.

.. currentmodule:: rinoh

.. autosummary::
    :toctree: style
    :template: autosummary/style_class.rst
    :nosignatures:

    draw.LineStyle
    draw.ShapeStyle
    flowable.FlowableStyle
    flowable.LabeledFlowableStyle
    flowable.GroupedFlowablesStyle
    flowable.FloatStyle
    image.CaptionStyle
    image.FigureStyle
    index.IndexStyle
    paragraph.ParagraphStyle
    text.TextStyle
    inline.InlineFlowableStyle
    reference.ReferencingParagraphStyle
    reference.NoteMarkerStyle
    structure.SectionStyle
    structure.HeadingStyle
    structure.ListStyle
    structure.ListItemLabelStyle
    structure.TableOfContentsStyle
    structure.TableOfContentsEntryStyle
    structure.AdmonitionStyle
    structure.HorizontalRuleStyle
    table.TableStyle
    table.TableCellStyle
    table.TableCellBorderStyle
    table.TableCellBackgroundStyle
