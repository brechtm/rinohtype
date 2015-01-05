from rinoh import *


__all__ = ['matcher']


matcher = StyledMatcher()

matcher('body', ClassSelector(Paragraph))

matcher('monospaced', ClassSelector(StyledText, 'monospaced'))

matcher('error', ClassSelector(StyledText, 'error'))

matcher('hyperlink', ClassSelector(StyledText, 'link'))

matcher('literal', ClassSelector(Paragraph, 'literal'))

matcher('block quote', ClassSelector(GroupedFlowables, 'block quote'))

matcher('attribution', ClassSelector(Paragraph, 'attribution'))

matcher('nested line block',
       ContextSelector(ClassSelector(GroupedFlowables, 'line block'),
                       ClassSelector(GroupedFlowables, 'line block')))

matcher('title', ClassSelector(Paragraph, 'title'))

matcher('subtitle', ClassSelector(Paragraph, 'subtitle'))

matcher('author', ClassSelector(Paragraph, 'author'))

matcher('affiliation', ClassSelector(Paragraph, 'affiliation'))

for i in range(1, 6):
    matcher('heading level {}'.format(i), ClassSelector(Heading, level=i))
    matcher('unnumbered heading level {}'.format(i),
            ClassSelector(Heading, 'unnumbered', level=i))

matcher('topic', ClassSelector(GroupedFlowables, 'topic'))

matcher('topic title', ContextSelector(ClassSelector(GroupedFlowables, 'topic'),
                                      ClassSelector(Paragraph, 'title')))

matcher('rubric', ClassSelector(Paragraph, 'rubric'))

matcher('sidebar frame', ClassSelector(Framed, 'sidebar'))

matcher('sidebar title', ContextSelector(ClassSelector(Framed, 'sidebar'),
                                        ClassSelector(GroupedFlowables),
                                        ClassSelector(Paragraph, 'title')))

matcher('sidebar subtitle', ContextSelector(ClassSelector(Framed, 'sidebar'),
                                           ClassSelector(GroupedFlowables),
                                           ClassSelector(Paragraph, 'subtitle')))

matcher('list item number', ContextSelector(ClassSelector(ListItem),
                                           ClassSelector(Paragraph)))

matcher('enumerated list', ClassSelector(List, 'enumerated'))

matcher('nested enumerated list', ContextSelector(ClassSelector(ListItem),
                                                 ClassSelector(List,
                                                               'enumerated')))

matcher('bulleted list', ClassSelector(List, 'bulleted'))

matcher('nested bulleted list', ContextSelector(ClassSelector(ListItem),
                                               ClassSelector(List, 'bulleted')))

matcher('list item body', ContextSelector(ClassSelector(ListItem),
                                         ClassSelector(GroupedFlowables)))

matcher('list item paragraph', ContextSelector(ClassSelector(ListItem),
                                              ClassSelector(GroupedFlowables),
                                              ClassSelector(Paragraph)))

matcher('definition list', ClassSelector(DefinitionList))

matcher('definition term', ClassSelector(DefinitionTerm))

matcher('definition term classifier', ClassSelector(StyledText, 'classifier'))

matcher('definition', ContextSelector(ClassSelector(DefinitionList),
                                     ClassSelector(GroupedFlowables)))


# field lists

matcher('field name', ClassSelector(Paragraph, 'field_name'))


# option lists

matcher('option', ClassSelector(Paragraph, 'option_group'))

matcher('option string', ClassSelector(MixedStyledText, 'option_string'))

matcher('option argument', ClassSelector(MixedStyledText, 'option_arg'))

matcher('admonition', ClassSelector(Framed, 'admonition'))

matcher('admonition title', ContextSelector(ClassSelector(Framed, 'admonition'),
                                           ClassSelector(GroupedFlowables),
                                           ClassSelector(Paragraph, 'title')))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = ContextSelector(ClassSelector(Framed, 'admonition',
                                             admonition_type=admonition_type),
                               ClassSelector(GroupedFlowables),
                               ClassSelector(Paragraph, 'title'))
    matcher(admonition_type + ' admonition title', selector)


matcher('header', ClassSelector(Header))

matcher('footer', ClassSelector(Footer))

matcher('footnote marker', ClassSelector(NoteMarkerBase, 'footnote'))

matcher('citation marker', ClassSelector(NoteMarkerBase, 'citation'))

matcher('footnote paragraph', ContextSelector(ClassSelector(Note),
                                             ClassSelector(GroupedFlowables),
                                             ClassSelector(Paragraph)))

matcher('footnote label', ContextSelector(ClassSelector(Note),
                                         ClassSelector(Paragraph)))

matcher('figure', ClassSelector(Figure))


matcher('image', ClassSelector(Image))

matcher('figure caption', ContextSelector(ClassSelector(Figure),
                                         ClassSelector(Caption)))

matcher('figure legend',
       ContextSelector(ClassSelector(Figure),
                       ClassSelector(GroupedFlowables, 'legend')))

matcher('figure legend paragraph',
       ContextSelector(ClassSelector(Figure),
                       ClassSelector(GroupedFlowables, 'legend'),
                       ClassSelector(Paragraph)))

matcher('table of contents', ClassSelector(TableOfContents))

matcher('toc level 1', ClassSelector(TableOfContentsEntry, depth=1))

matcher('toc level 2', ClassSelector(TableOfContentsEntry, depth=2))

matcher('toc level 3', ClassSelector(TableOfContentsEntry, depth=3))

matcher('L3 toc level 3', ContextSelector(ClassSelector(TableOfContents, level=2),
                                         ClassSelector(TableOfContentsEntry, depth=3)))

matcher('table', ClassSelector(Table))

matcher('table cell',
       ContextSelector(ClassSelector(Table),
                       ClassSelector(TableSection),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell)))

matcher('table body cell background on even row',
       ContextSelector(ClassSelector(TableBody),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell,
                                     row_index=slice(0, None, 2), rowspan=1),
                       ClassSelector(TableCellBackground)))

matcher('table body cell paragraph',
       ContextSelector(ClassSelector(TableBody),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell),
                       ...,
                       ClassSelector(Paragraph)))

matcher('table body cell list item number',
       ContextSelector(ClassSelector(TableBody),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell),
                       ...,
                       ClassSelector(ListItem),
                       ClassSelector(Paragraph)))

matcher('table head cell paragraph',
       ContextSelector(ClassSelector(TableHead),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell),
                       ClassSelector(Paragraph)))

matcher('table top border',
       ContextSelector(ClassSelector(TableHead),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell, row_index=0),
                       ClassSelector(TableCellBorder, position='top')))

matcher('table bottom border',
       ContextSelector(ClassSelector(TableBody),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell, row_index=-1),
                       ClassSelector(TableCellBorder, position='bottom')))

matcher('table head inner border',
       ContextSelector(ClassSelector(TableHead),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell),
                       ClassSelector(TableCellBorder, position='bottom')))

matcher('table body top border',
       ContextSelector(ClassSelector(TableBody),
                       ClassSelector(TableRow),
                       ClassSelector(TableCell, row_index=0),
                       ClassSelector(TableCellBorder, position='top')))

matcher('horizontal rule', ClassSelector(HorizontalRule))
