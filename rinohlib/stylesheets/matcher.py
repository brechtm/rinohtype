import rinoh as rt
from rinoh import StyledMatcher, ClassSelector, ContextSelector


matcher = StyledMatcher()

matcher('body', ClassSelector(rt.Paragraph))

matcher('monospaced', ClassSelector(rt.StyledText, 'monospaced'))

matcher('error', ClassSelector(rt.StyledText, 'error'))

matcher('hyperlink', ClassSelector(rt.StyledText, 'link'))

matcher('literal', ClassSelector(rt.Paragraph, 'literal'))

matcher('block quote', ClassSelector(rt.GroupedFlowables, 'block quote'))

matcher('attribution', ClassSelector(rt.Paragraph, 'attribution'))

matcher('nested line block',
       ContextSelector(ClassSelector(rt.GroupedFlowables, 'line block'),
                       ClassSelector(rt.GroupedFlowables, 'line block')))

matcher('title', ClassSelector(rt.Paragraph, 'title'))

matcher('subtitle', ClassSelector(rt.Paragraph, 'subtitle'))

matcher('author', ClassSelector(rt.Paragraph, 'author'))

matcher('affiliation', ClassSelector(rt.Paragraph, 'affiliation'))

for i in range(1, 6):
    matcher('heading level {}'.format(i), ClassSelector(rt.Heading, level=i))
    matcher('unnumbered heading level {}'.format(i),
            ClassSelector(rt.Heading, 'unnumbered', level=i))

matcher('topic', ClassSelector(rt.GroupedFlowables, 'topic'))

matcher('topic title', ContextSelector(ClassSelector(rt.GroupedFlowables, 'topic'),
                                      ClassSelector(rt.Paragraph, 'title')))

matcher('rubric', ClassSelector(rt.Paragraph, 'rubric'))

matcher('sidebar frame', ClassSelector(rt.Framed, 'sidebar'))

matcher('sidebar title', ContextSelector(ClassSelector(rt.Framed, 'sidebar'),
                                        ClassSelector(rt.GroupedFlowables),
                                        ClassSelector(rt.Paragraph, 'title')))

matcher('sidebar subtitle', ContextSelector(ClassSelector(rt.Framed, 'sidebar'),
                                           ClassSelector(rt.GroupedFlowables),
                                           ClassSelector(rt.Paragraph, 'subtitle')))

matcher('list item number', ContextSelector(ClassSelector(rt.ListItem),
                                           ClassSelector(rt.Paragraph)))

matcher('enumerated list', ClassSelector(rt.List, 'enumerated'))

matcher('nested enumerated list', ContextSelector(ClassSelector(rt.ListItem),
                                                 ClassSelector(rt.List,
                                                               'enumerated')))

matcher('bulleted list', ClassSelector(rt.List, 'bulleted'))

matcher('nested bulleted list', ContextSelector(ClassSelector(rt.ListItem),
                                               ClassSelector(rt.List, 'bulleted')))

matcher('list item body', ContextSelector(ClassSelector(rt.ListItem),
                                         ClassSelector(rt.GroupedFlowables)))

matcher('list item paragraph', ContextSelector(ClassSelector(rt.ListItem),
                                              ClassSelector(rt.GroupedFlowables),
                                              ClassSelector(rt.Paragraph)))

matcher('definition list', ClassSelector(rt.DefinitionList))

matcher('definition term', ClassSelector(rt.DefinitionTerm))

matcher('definition term classifier', ClassSelector(rt.StyledText, 'classifier'))

matcher('definition', ContextSelector(ClassSelector(rt.DefinitionList),
                                     ClassSelector(rt.GroupedFlowables)))


# field lists

matcher('field name', ClassSelector(rt.Paragraph, 'field_name'))


# option lists

matcher('option', ClassSelector(rt.Paragraph, 'option_group'))

matcher('option string', ClassSelector(rt.MixedStyledText, 'option_string'))

matcher('option argument', ClassSelector(rt.MixedStyledText, 'option_arg'))

matcher('admonition', ClassSelector(rt.Framed, 'admonition'))

matcher('admonition title', ContextSelector(ClassSelector(rt.Framed, 'admonition'),
                                           ClassSelector(rt.GroupedFlowables),
                                           ClassSelector(rt.Paragraph, 'title')))

for admonition_type in ('attention', 'caution', 'danger', 'error', 'warning'):
    selector = ContextSelector(ClassSelector(rt.Framed, 'admonition',
                                             admonition_type=admonition_type),
                               ClassSelector(rt.GroupedFlowables),
                               ClassSelector(rt.Paragraph, 'title'))
    matcher(admonition_type + ' admonition title', selector)


matcher('header', ClassSelector(rt.Header))

matcher('footer', ClassSelector(rt.Footer))

matcher('footnote marker', ClassSelector(rt.NoteMarkerBase, 'footnote'))

matcher('citation marker', ClassSelector(rt.NoteMarkerBase, 'citation'))

matcher('footnote paragraph', ContextSelector(ClassSelector(rt.Note),
                                             ClassSelector(rt.GroupedFlowables),
                                             ClassSelector(rt.Paragraph)))

matcher('footnote label', ContextSelector(ClassSelector(rt.Note),
                                         ClassSelector(rt.Paragraph)))

matcher('figure', ClassSelector(rt.Figure))


matcher('image', ClassSelector(rt.Image))

matcher('figure caption', ContextSelector(ClassSelector(rt.Figure),
                                         ClassSelector(rt.Caption)))

matcher('figure legend',
       ContextSelector(ClassSelector(rt.Figure),
                       ClassSelector(rt.GroupedFlowables, 'legend')))

matcher('figure legend paragraph',
       ContextSelector(ClassSelector(rt.Figure),
                       ClassSelector(rt.GroupedFlowables, 'legend'),
                       ClassSelector(rt.Paragraph)))

matcher('table of contents', ClassSelector(rt.TableOfContents))

matcher('toc level 1', ClassSelector(rt.TableOfContentsEntry, depth=1))

matcher('toc level 2', ClassSelector(rt.TableOfContentsEntry, depth=2))

matcher('toc level 3', ClassSelector(rt.TableOfContentsEntry, depth=3))

matcher('L3 toc level 3', ContextSelector(ClassSelector(rt.TableOfContents, level=2),
                                         ClassSelector(rt.TableOfContentsEntry, depth=3)))

matcher('table', ClassSelector(rt.Table))

matcher('table cell',
       ContextSelector(ClassSelector(rt.Table),
                       ClassSelector(rt.TableSection),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell)))

matcher('table body cell background on even row',
       ContextSelector(ClassSelector(rt.TableBody),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell,
                                     row_index=slice(0, None, 2), rowspan=1),
                       ClassSelector(rt.TableCellBackground)))

matcher('table body cell paragraph',
       ContextSelector(ClassSelector(rt.TableBody),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell),
                       ...,
                       ClassSelector(rt.Paragraph)))

matcher('table body cell list item number',
       ContextSelector(ClassSelector(rt.TableBody),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell),
                       ...,
                       ClassSelector(rt.ListItem),
                       ClassSelector(rt.Paragraph)))

matcher('table head cell paragraph',
       ContextSelector(ClassSelector(rt.TableHead),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell),
                       ClassSelector(rt.Paragraph)))

matcher('table top border',
       ContextSelector(ClassSelector(rt.TableHead),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell, row_index=0),
                       ClassSelector(rt.TableCellBorder, position='top')))

matcher('table bottom border',
       ContextSelector(ClassSelector(rt.TableBody),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell, row_index=-1),
                       ClassSelector(rt.TableCellBorder, position='bottom')))

matcher('table head inner border',
       ContextSelector(ClassSelector(rt.TableHead),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell),
                       ClassSelector(rt.TableCellBorder, position='bottom')))

matcher('table body top border',
       ContextSelector(ClassSelector(rt.TableBody),
                       ClassSelector(rt.TableRow),
                       ClassSelector(rt.TableCell, row_index=0),
                       ClassSelector(rt.TableCellBorder, position='top')))

matcher('horizontal rule', ClassSelector(rt.HorizontalRule))
