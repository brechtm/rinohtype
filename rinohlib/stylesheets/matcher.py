from rinoh.style import StyledMatcher
from rinoh.styleds import *

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

matcher('hyperlink', StyledText.like('link'))

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

for i in range(1, 6):
    matcher('heading level {}'.format(i), Heading.like(level=i))
    matcher('unnumbered heading level {}'.format(i),
            Heading.like('unnumbered', level=i))

matcher('other heading levels', Heading)

matcher('topic', GroupedFlowables.like('topic'))

matcher('topic title', GroupedFlowables.like('topic') / Paragraph.like('title'))

matcher('rubric', Paragraph.like('rubric'))

matcher('sidebar frame', Framed.like('sidebar'))

matcher('sidebar title', Framed.like('sidebar')
                         / GroupedFlowables
                         / Paragraph.like('title'))

matcher('sidebar subtitle', Framed.like('sidebar')
                            / GroupedFlowables
                            / Paragraph.like('subtitle'))

matcher('list item number', ListItem / Paragraph)

matcher('enumerated list', List.like('enumerated'))

matcher('nested enumerated list', ListItem / List.like('enumerated'))

matcher('bulleted list', List.like('bulleted'))

matcher('nested bulleted list', ListItem / List.like('bulleted'))

matcher('list item body', ListItem / GroupedFlowables)

matcher('list item paragraph', ListItem / GroupedFlowables / Paragraph)

matcher('definition list', DefinitionList)

matcher('definition term', DefinitionTerm)

matcher('definition term classifier', StyledText.like('classifier'))

matcher('definition', DefinitionList / GroupedFlowables)


# field lists

matcher('field name', Paragraph.like('field_name'))


# option lists

matcher('option', Paragraph.like('option_group'))

matcher('option string', MixedStyledText.like('option_string'))

matcher('option argument', MixedStyledText.like('option_arg'))

matcher('admonition', Framed.like('admonition'))

matcher('admonition title', Framed.like('admonition')
                            / GroupedFlowables
                            / Paragraph.like('title'))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = (Framed.like('admonition', admonition_type=admonition_type)
                / GroupedFlowables
                / Paragraph.like('title'))
    matcher(admonition_type + ' admonition title', selector)


matcher('header', Header)

matcher('footer', Footer)

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

matcher('table of contents section', Section.like('table of contents'))

matcher('table of contents', TableOfContents)

matcher('toc level 1', TableOfContentsEntry.like(depth=1))

matcher('toc level 2', TableOfContentsEntry.like(depth=2))

matcher('toc level 3', TableOfContentsEntry.like(depth=3))

matcher('L3 toc level 3', TableOfContents.like(level=2)
                          / TableOfContentsEntry.like(depth=3))

matcher('table', Table)

matcher('table cell', Table / TableSection / TableRow / TableCell)

matcher('table body cell background on even row',
        TableBody
        / TableRow
        / TableCell.like(row_index=slice(0, None, 2), rowspan=1)
        / TableCellBackground)

matcher('table body cell paragraph',
        TableBody / TableRow / TableCell / ... / Paragraph)

matcher('table first column paragraph',
        TableBody / TableRow / TableCell.like(column_index=0) / ... / Paragraph)

matcher('table body cell list item number',
        TableBody / TableRow / TableCell / ... / ListItem / Paragraph)

matcher('table head cell paragraph',
        TableHead / TableRow / TableCell / Paragraph)

matcher('table top border', TableHead
                            / TableRow
                            / TableCell.like(row_index=0)
                            / TableCellBorder.like(position='top'))

matcher('table bottom border', TableBody
                               / TableRow
                               / TableCell.like(row_index=-1)
                               / TableCellBorder.like(position='bottom'))

matcher('table head inner border', TableHead
                                   / TableRow
                                   / TableCell
                                   / TableCellBorder.like(position='bottom'))

matcher('table body top border', TableBody
                                 / TableRow
                                 / TableCell.like(row_index=0)
                                 / TableCellBorder.like(position='top'))

matcher('horizontal rule', HorizontalRule)
