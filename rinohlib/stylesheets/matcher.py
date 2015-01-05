from rinoh import *


__all__ = ['matcher']


matcher = StyledMatcher()

matcher('body', Paragraph)

matcher('monospaced', StyledText.like('monospaced'))

matcher('error', StyledText.like('error'))

matcher('hyperlink', StyledText.like('link'))

matcher('literal', Paragraph.like('literal'))

matcher('block quote', GroupedFlowables.like('block quote'))

matcher('attribution', Paragraph.like('attribution'))

matcher('nested line block',
       ContextSelector(GroupedFlowables.like('line block'),
                       GroupedFlowables.like('line block')))

matcher('title', Paragraph.like('title'))

matcher('subtitle', Paragraph.like('subtitle'))

matcher('author', Paragraph.like('author'))

matcher('affiliation', Paragraph.like('affiliation'))

for i in range(1, 6):
    matcher('heading level {}'.format(i), Heading.like(level=i))
    matcher('unnumbered heading level {}'.format(i),
            Heading.like('unnumbered', level=i))

matcher('topic', GroupedFlowables.like('topic'))

matcher('topic title', ContextSelector(GroupedFlowables.like('topic'),
                                      Paragraph.like('title')))

matcher('rubric', Paragraph.like('rubric'))

matcher('sidebar frame', Framed.like('sidebar'))

matcher('sidebar title', ContextSelector(Framed.like('sidebar'),
                                        GroupedFlowables,
                                        Paragraph.like('title')))

matcher('sidebar subtitle', ContextSelector(Framed.like('sidebar'),
                                           GroupedFlowables,
                                           Paragraph.like('subtitle')))

matcher('list item number', ContextSelector(ListItem,
                                           Paragraph))

matcher('enumerated list', List.like('enumerated'))

matcher('nested enumerated list', ContextSelector(ListItem,
                                                  List.like('enumerated')))

matcher('bulleted list', List.like('bulleted'))

matcher('nested bulleted list', ContextSelector(ListItem,
                                               List.like('bulleted')))

matcher('list item body', ContextSelector(ListItem,
                                         GroupedFlowables))

matcher('list item paragraph', ContextSelector(ListItem,
                                              GroupedFlowables,
                                              Paragraph))

matcher('definition list', DefinitionList)

matcher('definition term', DefinitionTerm)

matcher('definition term classifier', StyledText.like('classifier'))

matcher('definition', ContextSelector(DefinitionList,
                                     GroupedFlowables))


# field lists

matcher('field name', Paragraph.like('field_name'))


# option lists

matcher('option', Paragraph.like('option_group'))

matcher('option string', MixedStyledText.like('option_string'))

matcher('option argument', MixedStyledText.like('option_arg'))

matcher('admonition', Framed.like('admonition'))

matcher('admonition title', ContextSelector(Framed.like('admonition'),
                                           GroupedFlowables,
                                           Paragraph.like('title')))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = ContextSelector(Framed.like('admonition',
                                             admonition_type=admonition_type),
                               GroupedFlowables,
                               Paragraph.like('title'))
    matcher(admonition_type + ' admonition title', selector)


matcher('header', Header)

matcher('footer', Footer)

matcher('footnote marker', NoteMarkerBase.like('footnote'))

matcher('citation marker', NoteMarkerBase.like('citation'))

matcher('footnote paragraph', ContextSelector(Note,
                                             GroupedFlowables,
                                             Paragraph))

matcher('footnote label', ContextSelector(Note,
                                         Paragraph))

matcher('figure', Figure)


matcher('image', Image)

matcher('figure caption', ContextSelector(Figure,
                                         Caption))

matcher('figure legend',
       ContextSelector(Figure,
                       GroupedFlowables.like('legend')))

matcher('figure legend paragraph',
       ContextSelector(Figure,
                       GroupedFlowables.like('legend'),
                       Paragraph))

matcher('table of contents', TableOfContents)

matcher('toc level 1', TableOfContentsEntry.like(depth=1))

matcher('toc level 2', TableOfContentsEntry.like(depth=2))

matcher('toc level 3', TableOfContentsEntry.like(depth=3))

matcher('L3 toc level 3', ContextSelector(TableOfContents.like(level=2),
                                         TableOfContentsEntry.like(depth=3)))

matcher('table', Table)

matcher('table cell',
       ContextSelector(Table,
                       TableSection,
                       TableRow,
                       TableCell))

matcher('table body cell background on even row',
       ContextSelector(TableBody,
                       TableRow,
                       TableCell.like(row_index=slice(0, None, 2), rowspan=1),
                       TableCellBackground))

matcher('table body cell paragraph',
       ContextSelector(TableBody,
                       TableRow,
                       TableCell,
                       ...,
                       Paragraph))

matcher('table body cell list item number',
       ContextSelector(TableBody,
                       TableRow,
                       TableCell,
                       ...,
                       ListItem,
                       Paragraph))

matcher('table head cell paragraph',
       ContextSelector(TableHead,
                       TableRow,
                       TableCell,
                       Paragraph))

matcher('table top border',
       ContextSelector(TableHead,
                       TableRow,
                       TableCell.like(row_index=0),
                       TableCellBorder.like(position='top')))

matcher('table bottom border',
       ContextSelector(TableBody,
                       TableRow,
                       TableCell.like(row_index=-1),
                       TableCellBorder.like(position='bottom')))

matcher('table head inner border',
       ContextSelector(TableHead,
                       TableRow,
                       TableCell,
                       TableCellBorder.like(position='bottom')))

matcher('table body top border',
       ContextSelector(TableBody,
                       TableRow,
                       TableCell.like(row_index=0),
                       TableCellBorder.like(position='top')))

matcher('horizontal rule', HorizontalRule)
