from rinoh.style import StyledMatcher
from rinoh.styleds import *

from rinohlib.templates.base import FrontMatter


__all__ = ['matcher']


matcher = StyledMatcher()

matcher('title page title', Paragraph.like('title page title'))

matcher('title page subtitle', Paragraph.like('title page subtitle'))

matcher('title page author', Paragraph.like('title page author'))

matcher('title page date', Paragraph.like('title page date'))

matcher('title page extra', Paragraph.like('title page extra'))

matcher('body', Paragraph)

matcher('emphasis', StyledText.like('emphasis'))

matcher('strong', StyledText.like('strong'))

matcher('title reference', StyledText.like('title reference'))

matcher('monospaced', StyledText.like('monospaced'))

matcher('error', StyledText.like('error'))

matcher('internal hyperlink', StyledText.like('internal link'))

matcher('external hyperlink', StyledText.like('external link'))

matcher('broken hyperlink', StyledText.like('broken link'))

matcher('literal', Paragraph.like('literal'))

matcher('block quote', GroupedFlowables.like('block quote'))

matcher('attribution', Paragraph.like('attribution'))

matcher('line block line', Paragraph.like('line block line'))

matcher('nested line block', GroupedFlowables.like('line block')
                             / GroupedFlowables.like('line block'))

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

matcher('topic', GroupedFlowables.like('topic'))

matcher('abstract', GroupedFlowables.like('abstract'))

matcher('abstract paragraph',
        GroupedFlowables.like('abstract') / Paragraph)

matcher('topic title', GroupedFlowables.like('topic') / Paragraph.like('title'))

matcher('rubric', Paragraph.like('rubric'))

matcher('sidebar frame', GroupedFlowables.like('sidebar'))

matcher('sidebar title', GroupedFlowables.like('sidebar')
                         / Paragraph.like('title'))

matcher('sidebar subtitle', GroupedFlowables.like('sidebar')
                            / Paragraph.like('subtitle'))

matcher('list item label', ListItemLabel)

matcher('enumerated list', List.like('enumerated'))

matcher('enumerated list item label', List.like('enumerated')
                                      / ListItem / ListItemLabel)

matcher('nested enumerated list', ListItem / List.like('enumerated'))

matcher('bulleted list', List.like('bulleted'))

matcher('bulleted list item label', List.like('bulleted')
                                    / ListItem / ListItemLabel)

matcher('nested bulleted list', ListItem / List.like('bulleted'))

matcher('list item body', ListItem / GroupedFlowables)

matcher('list item paragraph', ListItem / ... / Paragraph)

matcher('definition list', DefinitionList)

matcher('definition term', DefinitionTerm)

matcher('definition term paragraph', DefinitionTerm / ... / Paragraph)

matcher('definition term classifier',
        DefinitionTerm / ... /StyledText.like('classifier'))

matcher('definition', Definition)

# (Sphinx) version added/changed & deprecated

matcher('versionmodified', StyledText.like(classes=['versionmodified']))

# (Sphinx) object descriptions

desc = DefinitionList.like('object description')

matcher('object description', desc)

matcher('object signature', desc / DefinitionTerm / ... / Paragraph)

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

matcher('object description content', desc / GroupedFlowables)


# (Sphinx) production list

matcher('production list', FieldList.like('production list'))

matcher('production',
        FieldList.like('production list') / LabeledFlowable.like('production'))

matcher('token name',
        FieldList.like('production list') / ... / Paragraph.like('token'))

matcher('token definition',
        FieldList.like('production list') / ... / Paragraph.like('definition'))


# field lists

matcher('field name', Paragraph.like('field_name'))


# option lists

matcher('option', Paragraph.like('option_group'))

matcher('option string', MixedStyledText.like('option_string'))

matcher('option argument', MixedStyledText.like('option_arg'))

matcher('admonition', GroupedFlowables.like('admonition'))

matcher('admonition title', GroupedFlowables.like('admonition')
                            / Paragraph.like('title'))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = (GroupedFlowables.like('admonition',
                                      admonition_type=admonition_type)
                / Paragraph.like('title'))
    matcher(admonition_type + ' admonition title', selector)


matcher('header', Header)

matcher('line under header', HorizontalRule.like('header'))

matcher('footer', Footer)

matcher('line above footer', HorizontalRule.like('footer'))


matcher('footnote marker', NoteMarkerBase.like('footnote'))

matcher('citation marker', NoteMarkerBase.like('citation'))

matcher('footnote paragraph', Note / GroupedFlowables / Paragraph)

matcher('footnote label', Note / Paragraph)

matcher('figure', Figure)


matcher('image', Image)

matcher('caption', Caption)

matcher('figure legend', Figure / GroupedFlowables.like('legend'))

matcher('figure legend paragraph', Figure
                                   / GroupedFlowables.like('legend')
                                   / Paragraph)

matcher('front matter section', FrontMatter > Section.like(level=1))

matcher('front matter section heading', FrontMatter > Section.like(level=1) / Heading)

matcher('table of contents section', Section.like('table of contents'))

matcher('table of contents title',
        Section.like('table of contents', level=1) / Heading)

matcher('table of contents', TableOfContents)

matcher('toc level 1', TableOfContentsEntry.like(depth=1))

matcher('toc level 2', TableOfContentsEntry.like(depth=2))

matcher('toc level 3', TableOfContentsEntry.like(depth=3))

matcher('L3 toc level 3', TableOfContents.like(level=2)
                          / TableOfContentsEntry.like(depth=3))

matcher('table with caption', TableWithCaption)

matcher('table', Table)

matcher('table cell', Table / TableSection / TableRow / TableCell)

matcher('table body cell background on even row',
        TableBody
        / TableRow
        / TableCell.like(row_index=slice(0, None, 2), rowspan=1)
        / TableCellBackground)

matcher('table body cell background on odd row',
        TableBody
        / TableRow
        / TableCell.like(row_index=slice(0, None, 1), rowspan=1)
        / TableCellBackground)

matcher('table body cell paragraph',
        TableBody / TableRow / TableCell / ... / Paragraph)

matcher('table first column paragraph',
        TableBody / TableRow / TableCell.like(column_index=0) / ... / Paragraph)

matcher('table body cell list item number',
        TableBody / TableRow / TableCell / ... / ListItem / Paragraph)

matcher('table head cell paragraph',
        TableHead / TableRow / TableCell / Paragraph)

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

matcher('table head cell left border', TableHead
                                       / TableRow
                                       / TableCell
                                       / TableCellBorder.like(position='left'))

matcher('table head cell right border', TableHead
                                        / TableRow
                                        / TableCell
                                        / TableCellBorder.like(position='right'))

matcher('table head bottom border', TableHead
                                    / TableRow
                                    / TableCell.like(row_index=-1)
                                    / TableCellBorder.like(position='bottom'))

matcher('table head left border', TableHead
                                  / TableRow
                                  / TableCell.like(column_index=0)
                                  / TableCellBorder.like(position='left'))

matcher('table head right border', TableHead
                                   / TableRow
                                   / TableCell.like(column_index=-1)
                                   / TableCellBorder.like(position='right'))

matcher('table body top border', TableBody
                                 / TableRow
                                 / TableCell.like(row_index=0)
                                 / TableCellBorder.like(position='top'))

matcher('table body left border', TableBody
                                  / TableRow
                                  / TableCell.like(column_index=0)
                                  / TableCellBorder.like(position='left'))

matcher('table body right border', TableBody
                                   / TableRow
                                   / TableCell.like(column_index=-1)
                                   / TableCellBorder.like(position='right'))

matcher('horizontal rule', HorizontalRule)
