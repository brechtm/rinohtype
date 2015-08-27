# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.frontend.xml import element_factory


class DocBookReader(object):
    def parse(self, file):
        filename = getattr(file, 'name', None)
        doctree =
        return self.from_doctree(doctree)

    @staticmethod
    def replace_secondary_ids(tree):
        id_aliases = {}
        for node in tree.traverse():
            try:
                primary_id, *alias_ids = node.attributes['ids']
                for alias_id in alias_ids:
                    id_aliases[alias_id] = primary_id
            except (AttributeError, KeyError, ValueError):
                pass
        # replace alias IDs used in references with the corresponding primary ID
        for node in tree.traverse():
            try:
                refid = node.get('refid')
                if refid in id_aliases:
                    node.attributes['refid'] = id_aliases[refid]
            except AttributeError:
                pass

    def from_doctree(self, doctree):
        self.replace_secondary_ids(doctree)
        mapped_tree = CustomElement.map_node(doctree.document)
        flowables = [child.flowable() for child in mapped_tree.getchildren()]
        return flowables
