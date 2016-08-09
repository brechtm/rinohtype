from rinoh.reference import TITLE, PAGE, NUMBER, REFERENCE
from rinoh.style import StyledMatcher, SelectorByName
from rinoh.styleds import *


__all__ = ['matcher']


matcher = StyledMatcher({

    # title page items

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

    'italic': StyledText.like('italic'),
    'bold': StyledText.like('bold'),
    'emphasis': StyledText.like('emphasis'),
    'strong': StyledText.like('strong'),
    'literal strong': StyledText.like('literal strong'),
    'quote': StyledText.like('quote'),
    'file path': StyledText.like('file path'),
    'window title': StyledText.like('window title'),
    'UI control': StyledText.like('UI control'),
    'menu cascade': StyledText.like('menu cascade'),
    'draft comment': StyledText.like('draft comment'),
    'title reference': StyledText.like('title reference'),
    'monospaced': StyledText.like('monospaced'),
    'error': StyledText.like('error'),

})

matcher('linked reference', Reference.like(link=True))
matcher('unlinked reference', Reference.like(link=False))

matcher('internal hyperlink', StyledText.like('internal link'))
matcher('external hyperlink', StyledText.like('external link'))
matcher('broken hyperlink', StyledText.like('broken link'))


# paragraphs

matcher('body', Paragraph)
matcher('code block', +CodeBlock)
matcher('attribution', Paragraph.like('attribution'))

matcher('block quote', GroupedFlowables.like('block quote'))
matcher('line block', GroupedFlowables.like('line block'))
matcher('nested line block', 'line block' / SelectorByName('line block'))
matcher('line block line', Paragraph.like('line block line'))


#

matcher('title', Paragraph.like('title'))
matcher('subtitle', Paragraph.like('subtitle'))
matcher('date', Paragraph.like('date'))
matcher('author', Paragraph.like('author'))
matcher('affiliation', Paragraph.like('affiliation'))

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

matcher('enumerated list', List.like('enumerated'))
matcher('enumerated list item', 'enumerated list' / ListItem)
matcher('enumerated list item label', 'enumerated list item' / ListItemLabel)
matcher('nested enumerated list', ListItem / 'enumerated list')

matcher('(table) enumerated list', TableCell / ... / 'enumerated list')
matcher('(table) enumerated list item', '(table) enumerated list' / ListItem)
matcher('(table) enumerated list item label', '(table) enumerated list item'
                                              / ListItemLabel)

matcher('bulleted list', List.like('bulleted'))
matcher('bulleted list item', 'bulleted list' / ListItem)
matcher('bulleted list item label', 'bulleted list item' / ListItemLabel)
matcher('nested bulleted list', ListItem / 'bulleted list')

matcher('(table) bulleted list', TableCell / ... / 'bulleted list')
matcher('(table) bulleted list item', '(table) bulleted list' / ListItem)
matcher('(table) bulleted list item label', '(table) bulleted list item'
                                            / ListItemLabel)

matcher('steps list', List.like('steps'))
matcher('steps list title', 'steps list' / Paragraph.like('title'))
matcher('steps list item', 'steps list' / ListItem)
matcher('steps list item label', 'steps list item' / ListItemLabel)

matcher('choices list', List.like('choices'))
matcher('choices list item', 'choices list' / ListItem)
matcher('choices list item label', 'choices list item' / ListItemLabel)

matcher('list item body', ListItem / GroupedFlowables)
matcher('list item paragraph', 'list item body' / Paragraph)

matcher('definition list', DefinitionList)
matcher('definition term', DefinitionTerm)
matcher('definition term paragraph', SelectorByName('definition term')
                                     / ... / Paragraph)
matcher('definition term classifier', SelectorByName('definition term')
                                      / ... /StyledText.like('classifier'))
matcher('definition', Definition)
matcher('definition paragraph', 'definition' / Paragraph)

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
matcher('related link title reference', rlpe / ReferenceField.like(type=TITLE))
matcher('related link page reference', rlpe / ReferenceField.like(type=PAGE))
matcher('related link number reference', rlpe /ReferenceField.like(type=NUMBER))
matcher('related link reference', rlpe / ReferenceField.like(type=REFERENCE))


# (Sphinx) version added/changed & deprecated

matcher('versionmodified', StyledText.like(classes=['versionmodified']))

# (Sphinx) object descriptions

desc = DefinitionList.like('object description')

matcher('object description', desc)
matcher('object definition term', desc / DefinitionTerm)
matcher('object signature', SelectorByName('object definition term') / Paragraph)
matcher('object name', desc / ... / StyledText.like('main object name'))
matcher('additional name part', desc / ... / StyledText.like('additional name part'))
matcher('object type', desc / ... / StyledText.like('type'))
matcher('object returns', desc / ... / StyledText.like('returns'))
matcher('object parentheses', desc / ... / StyledText.like('parentheses'))
matcher('object parameter list', desc / ... / StyledText.like('parameter list'))
matcher('object parameter', desc / ... / StyledText.like('parameter'))
matcher('object parameter (no emphasis)', desc / ... / StyledText.like('noemph parameter'))
matcher('object brackets', desc / ... / StyledText.like('brackets'))
matcher('object optional parameter', desc / ... / StyledText.like('optional'))
matcher('object annotation', desc / ... / StyledText.like('annotation'))
matcher('object description content', desc / Definition)
matcher('object description content paragraph',
            SelectorByName('object description content') / Paragraph)


# (Sphinx) production list

matcher('production list', FieldList.like('production list'))
matcher('production', 'production list' / LabeledFlowable.like('production'))
matcher('token name', SelectorByName('production list')
                      / ... / Paragraph.like('token'))
matcher('token definition', SelectorByName('production list')
                            / ... / Paragraph.like('definition'))


# field lists

matcher('field name', Paragraph.like('field_name'))


# option lists

matcher('option', Paragraph.like('option_group'))
matcher('option string', MixedStyledText.like('option_string'))
matcher('option argument', MixedStyledText.like('option_arg'))

matcher('admonition', Admonition)
matcher('admonition title', 'admonition' / Paragraph.like('title'))
matcher('admonition inline title', SelectorByName('admonition')
                                   / ... / StyledText.like('inline title'))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning',
                        'seealso', 'tip'):
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

matcher('figure', Figure)
matcher('image', Image)
matcher('inline image', InlineImage)
matcher('caption', Caption)
matcher('figure legend', 'figure' / GroupedFlowables.like('legend'))
matcher('figure legend paragraph', 'figure legend' / Paragraph)


# front matter

matcher('table of contents section', Section.like('table of contents'))
matcher('table of contents title', 'table of contents section'
                                   / Heading.like(level=1))
matcher('table of contents', TableOfContents)
matcher('toc level 1', TableOfContentsEntry.like(depth=1))
matcher('toc level 2', TableOfContentsEntry.like(depth=2))
matcher('toc level 3', TableOfContentsEntry.like(depth=3))
matcher('L3 toc level 3', TableOfContents.like(level=2)
                          / TableOfContentsEntry.like(depth=3))

# tables

matcher('table', Table)
matcher('table with caption', TableWithCaption)
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
