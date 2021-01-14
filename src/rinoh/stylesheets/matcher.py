from rinoh.style import StyledMatcher, SelectorByName
from rinoh.styleds import *


__all__ = ['matcher']


matcher = StyledMatcher({

    # title page items

    'title page rule': HorizontalRule.like('title page rule'),
    'title page logo': Image.like('title page logo'),
    'title page title': Paragraph.like('title page title'),
    'title page subtitle': Paragraph.like('title page subtitle'),
    'title page author': Paragraph.like('title page author'),
    'title page date': Paragraph.like('title page date'),
    'title page extra': Paragraph.like('title page extra'),

    # chapter titles

    'front matter section title': Paragraph.like('front matter section title'),
    'body matter chapter label': Paragraph.like('body matter chapter label'),
    'body matter chapter number': SelectorByName('body matter chapter label')
                                      / ... / StyledText.like('number'),
    'body matter chapter title': Paragraph.like('body matter chapter title'),

    # inline text

    'fallback': StyledText.like('_fallback_'),
    'italic': StyledText.like('italic'),
    'bold': StyledText.like('bold'),
    'monospaced': StyledText.like('monospaced'),
    'emphasis': StyledText.like('emphasis'),
    'strong': StyledText.like('strong'),
    'literal emphasis': StyledText.like('literal emphasis'),
    'literal strong': StyledText.like('literal strong'),
    'inline math': StyledText.like('math'),

    'quote': StyledText.like('quote'),
    'file path': StyledText.like('file path'),
    'keystrokes': StyledText.like('keystrokes'),
    'regular expression': StyledText.like('regular expression'),
    'code with variable': StyledText.like('code with variable'),
    'mail header': StyledText.like('mail header'),
    'MIME type': StyledText.like('MIME type'),
    'newsgroup': StyledText.like('newsgroup'),
    'command': StyledText.like('command'),
    'make variable': StyledText.like('make variable'),
    'program': StyledText.like('program'),
    'man page': StyledText.like('man page'),
    'window title': StyledText.like('window title'),
    'UI control': StyledText.like('UI control'),
    'UI control accelerator': SelectorByName('UI control') / ...
                              / StyledText.like('accelerator'),
    'menu cascade': StyledText.like('menu cascade'),
    'draft comment': StyledText.like('draft comment'),
    'title reference': StyledText.like('title reference'),
    'error': StyledText.like('error'),

})

matcher('linked reference', ReferenceBase.like(link=True))
matcher('unlinked reference', ReferenceBase.like(link=False))

matcher('internal hyperlink', StyledText.like('internal link'))
matcher('external hyperlink', StyledText.like('external link'))
matcher('broken hyperlink', StyledText.like('broken link'))

matcher('glossary inline definition',
        StyledText.like('glossary inline definition'))

# paragraphs

matcher('body', Paragraph)
matcher('code block', +CodeBlock)
matcher('code block caption', CodeBlockWithCaption / Caption)
matcher('math block', Paragraph.like('math'))
matcher('attribution', Paragraph.like('attribution'))
matcher('centered', Paragraph.like('centered'))
matcher('line block', Paragraph.like('line block'))

matcher('block quote', GroupedFlowables.like('block quote'))


#

matcher('chapter', Section.like(level=1))

for i in range(1, 6):
    matcher('heading level {}'.format(i), Heading.like(level=i))
    matcher('unnumbered heading level {}'.format(i),
            Heading.like('unnumbered', level=i))
matcher('other heading levels', Heading)

matcher('appendix', Section.like('appendix'))
for i in range(1, 6):
    matcher('appendix heading level {}'.format(i),
            'appendix' / Heading.like(level=i))

matcher('title', Paragraph.like('title'))

matcher('prerequisites', GroupedFlowables.like('prerequisites'))
matcher('prerequisites title', 'prerequisites' / Paragraph.like('title'))

matcher('post requirement', GroupedFlowables.like('post requirement'))

matcher('abstract', GroupedFlowables.like('abstract'))
matcher('abstract paragraph', 'abstract' / Paragraph)

matcher('example', GroupedFlowables.like('example'))
matcher('example title', 'example' / Paragraph.like('title'))

matcher('topic', GroupedFlowables.like('topic'))
matcher('topic title', 'topic' / Paragraph.like('title'))

matcher('rubric', Paragraph.like('rubric'))

matcher('sidebar', GroupedFlowables.like('sidebar'))
matcher('sidebar title', 'sidebar' / Paragraph.like('title'))
matcher('sidebar subtitle', 'sidebar' / Paragraph.like('subtitle'))


# lists

matcher('list item label', ListItemLabel)
matcher('list item body', ListItem / GroupedFlowables)
matcher('list item paragraph', 'list item body' / Paragraph)

matcher('enumerated list', List.like('enumerated'))
matcher('enumerated list item', 'enumerated list' / ListItem)
matcher('enumerated list item label', 'enumerated list item' / ListItemLabel)
matcher('nested enumerated list', SelectorByName('list item body')
                                  / 'enumerated list')

matcher('(table) enumerated list', TableCell / ... / 'enumerated list')
matcher('(table) enumerated list item', '(table) enumerated list' / ListItem)
matcher('(table) enumerated list item label', '(table) enumerated list item'
                                              / ListItemLabel)

matcher('bulleted list', List.like('bulleted'))
matcher('compact bulleted list', List.like('bulleted', compact=True))
matcher('bulleted list item', 'bulleted list' / ListItem)
matcher('bulleted list item label', 'bulleted list item' / ListItemLabel)
matcher('nested bulleted list', SelectorByName('list item body')
                                / 'bulleted list')

matcher('(table) bulleted list', TableCell / ... / 'bulleted list')
matcher('(table) bulleted list item', '(table) bulleted list' / ListItem)
matcher('(table) bulleted list item label', '(table) bulleted list item'
                                            / ListItemLabel)

matcher('steps list', List.like('steps'))
matcher('steps list title', 'steps list' / Paragraph.like('title'))
matcher('steps list item', 'steps list' / ListItem)
matcher('steps list item label', 'steps list item' / ListItemLabel)

matcher('unordered steps list', List.like('unordered steps'))
matcher('unordered steps list title', 'unordered steps list'
                                      / Paragraph.like('title'))
matcher('unordered steps list item', 'unordered steps list' / ListItem)
matcher('unordered steps list item label', 'unordered steps list item'
                                           / ListItemLabel)

matcher('choices list', List.like('choices'))
matcher('choices list item', 'choices list' / ListItem)
matcher('choices list item label', 'choices list item' / ListItemLabel)

matcher('definition list', DefinitionList)
matcher('definition list item', 'definition list' / LabeledFlowable)
matcher('definition term', 'definition list item'
                            / GroupedFlowables.like('definition term'))
matcher('definition term paragraph', SelectorByName('definition term')
                                     / ... / Paragraph)
matcher('definition term classifier', SelectorByName('definition term paragraph')
                                      / ... /StyledText.like('classifier'))
matcher('definition', 'definition list item'
                      / GroupedFlowables.like('definition'))
matcher('definition paragraph', 'definition' / Paragraph)


# (DITA) related links

matcher('related links', GroupedFlowables.like('related links'))
matcher('related links section title', 'related links'
                                       / Paragraph.like('title'))
matcher('related links list', 'related links' / List)
matcher('related links list item', 'related links list' / ListItem)
matcher('related links list item label', 'related links list item'
                                         / ListItemLabel)
rlp = matcher('related links list item paragraph',
                  SelectorByName('related links list item')
                  / ... / ReferencingParagraph)
rlpe = rlp / ...
matcher('related link title reference',rlpe / ReferenceField.like(type='title'))
matcher('related link page reference', rlpe / ReferenceField.like(type='page'))
matcher('related link number reference', rlpe /ReferenceField.like(type='number'))
matcher('related link reference', rlpe / ReferenceField.like(type='reference'))


# (Sphinx) version added/changed & deprecated

matcher('versionmodified', StyledText.like(classes=['versionmodified']))

# (Sphinx) object descriptions

matcher('object description', LabeledFlowable.like('object description'))
matcher('object signatures', 'object description'
                             / GroupedFlowables.like('signatures'))
matcher('object signature', 'object signatures' / Paragraph)
sig = SelectorByName('object signature') / ...
matcher('object name', sig / StyledText.like('main object name'))
matcher('additional name part', sig / StyledText.like('additional name part'))
matcher('object type', sig / StyledText.like('type'))
matcher('object returns', sig / StyledText.like('returns'))
matcher('object parentheses', sig / StyledText.like('parentheses'))
matcher('object parameter list', sig / StyledText.like('parameter list'))
matcher('object parameter', sig / StyledText.like('parameter'))
matcher('object parameter (no emphasis)',
        sig / StyledText.like('noemph parameter'))
matcher('object brackets', sig / StyledText.like('brackets'))
matcher('object optional parameter', sig / StyledText.like('optional'))
matcher('object annotation', sig / StyledText.like('annotation'))
matcher('object description content', 'object description'
                                      / GroupedFlowables.like('content'))
matcher('object description content paragraph', 'object description content'
                                                / Paragraph)


# (Sphinx) production list

matcher('production list', DefinitionList.like('production list'))
matcher('production', 'production list' / LabeledFlowable.like('production'))
matcher('token name', SelectorByName('production list')
                      / ... / Paragraph.like('token'))
matcher('token definition', SelectorByName('production list')
                            / ... / Paragraph.like('definition'))


# field lists

matcher('field list', DefinitionList.like('field list'))
matcher('field list item', 'field list' / LabeledFlowable)
matcher('field name', 'field list item' / Paragraph.like('field name'))


# option lists

matcher('option list', DefinitionList.like('option list'))
matcher('option list item', 'option list' / LabeledFlowable)
matcher('option', Paragraph.like('option_group'))
matcher('option string', MixedStyledText.like('option_string'))
matcher('option argument', MixedStyledText.like('option_arg'))

matcher('admonition', Admonition)
matcher('admonition title', 'admonition' / Paragraph.like('title'))
matcher('admonition inline title', SelectorByName('admonition')
                                   / ... / StyledText.like('inline title'))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'hint',
                        'important', 'note', 'tip', 'warning', 'seealso'):
    admonition_selector = Admonition.like(admonition_type=admonition_type)
    matcher(admonition_type + ' admonition', admonition_selector)
    selector = admonition_selector / Paragraph.like('title')
    matcher(admonition_type + ' admonition title', selector)
    matcher(admonition_type + ' admonition inline title',
            admonition_selector / ... / StyledText.like('inline title'))

# page header and footer

matcher('header', Header)
matcher('footer', Footer)


# footnotes & citations

matcher('footnote marker', NoteMarkerBase.like('footnote'))
matcher('citation marker', NoteMarkerBase.like('citation'))
matcher('footnote paragraph', Note / GroupedFlowables / Paragraph)
matcher('footnote label', Note / Paragraph)


# images & figures

matcher('image', Image)
matcher('inline image', InlineImage)
matcher('figure', Figure)
matcher('figure image', 'figure' / Image)
matcher('figure caption', 'figure' / Caption)
matcher('figure legend', 'figure' / GroupedFlowables.like('legend'))
matcher('figure legend paragraph', 'figure legend' / Paragraph)


# front matter

matcher('table of contents section', Section.like('table of contents'))
matcher('table of contents title', 'table of contents section'
                                   / Heading.like(level=1))
matcher('table of contents', TableOfContents)
matcher('local table of contents', TableOfContents.like(local=True))
matcher('toc level 1', TableOfContentsEntry.like(depth=1))
matcher('toc level 2', TableOfContentsEntry.like(depth=2))
matcher('toc level 3', TableOfContentsEntry.like(depth=3))
matcher('L3 toc level 3', TableOfContents.like(level=2)
                          / TableOfContentsEntry.like(depth=3))
matcher('toc linked reference', TableOfContentsEntry
                                / ... / ReferenceBase.like(link=True))

matcher('list of figures section', ListOfFiguresSection)
matcher('list of figures', ListOfFigures)
matcher('list of figures entry', 'list of figures' / ListOfEntry)

matcher('list of tables section', ListOfTablesSection)
matcher('list of tables', ListOfTables)
matcher('list of tables entry', 'list of tables' / ListOfEntry)


# tables

matcher('table', Table)
matcher('table with caption', TableWithCaption)
matcher('table caption', 'table with caption' / Caption)
matcher('choices table', Table.like('choice'))
matcher('table cell', Table / TableSection / TableRow / TableCell)
matcher('table body cell background on even row',
        TableBody / TableRow
        / TableCell.like(row_index=slice(1, None, 2), rowspan=1)
        / TableCellBackground)
matcher('table body cell background on odd row',
        TableBody / TableRow
        / TableCell.like(row_index=slice(0, None, 2), rowspan=1)
        / TableCellBackground)
matcher('table body cell paragraph', SelectorByName('table cell')
                                     / ... / Paragraph)
matcher('table first column paragraph',
        TableBody / TableRow / TableCell.like(column_index=0) / ... / Paragraph)
matcher('table body cell list item number', SelectorByName('table cell')
                                            / ... / ListItem / Paragraph)
matcher('table head cell', Table / TableHead / TableRow / TableCell)
matcher('table head cell paragraph', 'table head cell' / Paragraph)
matcher('table cell left border', TableCellBorder.like(position='left'))
matcher('table cell top border', TableCellBorder.like(position='top'))
matcher('table cell right border', TableCellBorder.like(position='right'))
matcher('table cell bottom border', TableCellBorder.like(position='bottom'))

matcher('table top border', TableHead
                            / TableRow
                            / TableCell.like(row_index=0)
                            / TableCellBorder.like(position='top'))
matcher('table bottom border', TableBody
                               / TableRow
                               / TableCell.like(row_index=-1)
                               / TableCellBorder.like(position='bottom'))
matcher('table left border', TableCell.like(column_index=0)
                             / TableCellBorder.like(position='left'))
matcher('table right border', TableCell.like(column_index=-1)
                              / TableCellBorder.like(position='right'))
matcher('table head cell left border', TableHead / TableRow / TableCell
                                       / TableCellBorder.like(position='left'))
matcher('table head cell right border', TableHead / TableRow / TableCell
                                        / TableCellBorder.like(position='right'))
matcher('table head bottom border', TableHead / TableRow
                                    / TableCell.like(row_index=-1)
                                    / TableCellBorder.like(position='bottom'))
matcher('table head left border', TableHead / TableRow
                                  / TableCell.like(column_index=0)
                                  / TableCellBorder.like(position='left'))
matcher('table head right border', TableHead / TableRow
                                   / TableCell.like(column_index=-1)
                                   / TableCellBorder.like(position='right'))
matcher('table body top border', TableBody / TableRow
                                 / TableCell.like(row_index=0)
                                 / TableCellBorder.like(position='top'))
matcher('table body left border', TableBody / TableRow
                                  / TableCell.like(column_index=0)
                                  / TableCellBorder.like(position='left'))
matcher('table body right border', TableBody / TableRow
                                   / TableCell.like(column_index=-1)
                                   / TableCellBorder.like(position='right'))



matcher('horizontal rule', HorizontalRule)


# index

matcher('index', Index)
matcher('index section label', IndexLabel)
matcher('level 1 index entry', IndexEntry.like(index_level=1))
matcher('level 2 index entry', IndexEntry.like(index_level=2))
matcher('level 3 index entry', IndexEntry.like(index_level=3))
matcher('level 4 index entry', IndexEntry.like(index_level=4))
matcher('domain index entry name', IndexEntry / ... / StyledText.like('domain'))


doc = ['The default matcher defines the following styles',
       '']
for style_name, selector in matcher.by_name.items():
    style_class = selector.get_styled_class(matcher).style_class
    doc.append('* {}: :class:`.{}`'.format(style_name, style_class.__name__))

matcher.__doc__ = '\n'.join(doc)
