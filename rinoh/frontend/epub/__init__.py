# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import xml.etree.ElementTree as etree

from zipfile import ZipFile

from ..xml.elementtree import Parser
from ..xml import (ElementTreeNode, ElementTreeInlineNode, ElementTreeBodyNode,
                   ElementTreeBodySubNode, ElementTreeGroupingNode,
                   ElementTreeDummyNode, ElementTreeNodeMeta)


__all__ = ['EPubNode', 'EPubInlineNode', 'EPubBodyNode', 'EPubBodySubNode',
           'EPubGroupingNode', 'EPubDummyNode',
           'EPubReader', 'BadEPub']


NS_MAP = dict(cnt='urn:oasis:names:tc:opendocument:xmlns:container',
              opf='http://www.idpf.org/2007/opf',
              dc='http://purl.org/dc/elements/1.1/',
              dcterms='http://purl.org/dc/terms/',
              xhtml='http://www.w3.org/1999/xhtml',
              epub='http://www.idpf.org/2007/ops')


class EPubNode(ElementTreeNode, metaclass=ElementTreeNodeMeta):
    NAMESPACE = NS_MAP['xhtml']


class EPubInlineNode(EPubNode, ElementTreeInlineNode):
    pass


class EPubBodyNode(EPubNode, ElementTreeBodyNode):
    pass


class EPubBodySubNode(EPubNode, ElementTreeBodySubNode):
    pass


class EPubGroupingNode(EPubNode, ElementTreeGroupingNode):
    pass


class EPubDummyNode(EPubNode, ElementTreeDummyNode):
    pass


from . import nodes


class BadEPub(Exception):
    def __init__(self):
        super().__init__('File is not an ePUB file')


class EPubReader(object):
    def parse(self, file):
        epub = ZipFile(file)
        if epub.read('mimetype') != 'application/epub+zip'.encode('ascii'):
            raise BadEPub
        with epub.open('META-INF/container.xml') as container_file:
            container = etree.parse(container_file).getroot()
        rootfiles = container.find('./cnt:rootfiles', NS_MAP)
        for rootfile in rootfiles.findall('./cnt:rootfile', NS_MAP):
            if rootfile.get('media-type') != 'application/oebps-package+xml':
                raise BadEPub
            content_path = rootfile.get('full-path')
            break   # only try the first rootfile
        content_dir = os.path.dirname(content_path)
        flowables = []
        with epub.open(content_path) as content_file:
            package = etree.parse(content_file).getroot()
            metadata = package.find('./opf:metadata', NS_MAP)
            print(metadata.find('./dc:title', NS_MAP).text)
            print(metadata.find('./dc:creator', NS_MAP).text)
            manifest = package.find('./opf:manifest', NS_MAP)
            items = {item.get('id'): item
                     for item in manifest.findall('./opf:item', NS_MAP)}
            spine = package.find('./opf:spine', NS_MAP)
            for itemref in spine.findall('./opf:itemref', NS_MAP):
                item = items[itemref.get('idref')]
                filename = os.path.join(content_dir, item.get('href'))
                if filename.endswith('pt04.html'):
                    break
                print(filename)
                with epub.open(filename) as xhtml_file:
                    xhtml_parser = Parser(EPubNode)
                    xhtml_tree = xhtml_parser.parse(xhtml_file)
                for flowable in self.from_doctree(xhtml_tree.getroot()):
                    flowables.append(flowable)
        return flowables

    def from_doctree(self, xhtml_root):
        xhtml_body = xhtml_root.find('./xhtml:body', NS_MAP)
        #self.replace_secondary_ids(doctree)
        mapped_tree = EPubNode.map_node(xhtml_body)
        return mapped_tree.children_flowables()
