# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .attribute import OptionSet, Attribute, OverrideDefault
from .flowable import GroupedFlowables
from .text import MixedStyledText, MixedStyledTextBase, TextStyle


__all__ = ['ShowDefinition', 'GlossaryTermStyle', 'GlossaryTerm', 'Glossary']


class ShowDefinition(OptionSet):
    """When to show the definition together with a glossary term in the text"""

    values = 'never', 'first', 'always'     # TODO: 'section'


class GlossaryTermStyle(TextStyle):
    show_definition = Attribute(ShowDefinition, ShowDefinition.FIRST,
                                'When to show the definition together with the'
                                ' glossary term in the text')


# TODO: inherit from Reference(Base) to hyperlink to the glossary entry
class GlossaryTerm(MixedStyledTextBase):
    style_class = GlossaryTermStyle

    def __init__(self, term, definition=None, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        term.parent = self
        self.term = term
        self.definition = definition

    def children(self, container):
        doc = container.document
        id = self.get_id(container.document)
        term_str = self.term.to_string(container)
        if self.definition and not doc.set_glossary(term_str, self.definition):
            self.warn("The definition for '{}' doesn't match the first"
                      " definition".format(term_str), container)
        yield self.term
        show_definition = self.get_style('show_definition', container)
        if show_definition == ShowDefinition.NEVER:
            return
        try:
            definition, first_id = doc.get_glossary(term_str, id)
        except KeyError:
            self.warn("No definition given for '{}' glossary term"
                      .format(term_str), container)
            return
        definition_text = MixedStyledText(definition, parent=self,
                                          style='glossary inline definition')
        if show_definition == ShowDefinition.FIRST:
            if first_id == id:
                yield definition_text
        elif show_definition == ShowDefinition.ALWAYS:
            yield definition_text


class Glossary(GroupedFlowables):
    pass

