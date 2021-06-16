from typing import cast

from docutils import nodes
from docutils.nodes import Text
from sphinx import addnodes
from sphinx.domains.citation import CitationDomain
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.nodes import NodeMatcher


class RinohCitationReferenceTransform(SphinxPostTransform):
    default_priority = 5  # before ReferencesResolver
    formats = ('pdf',)
    builders = ('rinoh',)

    def run(self, **kwargs) -> None:
        domain = cast(CitationDomain, self.env.get_domain('citation'))
        pending_xref = NodeMatcher(addnodes.pending_xref, refdomain='citation',
                                    reftype='ref')
        for node in self.document.traverse(pending_xref):
            doc, refid, _ = domain.citations.get(node['reftarget'], ('', '', 0))
            if doc:
                child = Text(node['reftarget'])
                citation_ref = nodes.citation_reference('', '', child,
                                                        docname=doc,
                                                        refid=refid)
                node.replace_self(citation_ref)
