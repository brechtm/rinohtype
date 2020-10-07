# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.document import DocumentTree, FakeContainer
from rinoh.image import Image
from rinoh.paragraph import Paragraph
from rinoh.reference import ReferencingParagraph
from rinoh.templates import Article


def test_image():
    stylesheet = None
    document = None

    nix_image1 = Image('dir/image.png')
    nix_image2 = Image('dir/subdir/image.png')
    win_image1 = Image(r'dir\image.png')
    win_image2 = Image(r'dir\subdir\image.png')
    nix_selector1 = Image.like(filename='dir/image.png')
    nix_selector2 = Image.like(filename='dir/subdir/image.png')
    win_selector1 = Image.like(filename=r'dir\image.png')
    win_selector2 = Image.like(filename=r'dir\subdir\image.png')
    assert nix_selector1.match(nix_image1, stylesheet, document)
    assert nix_selector2.match(nix_image2, stylesheet, document)
    assert nix_selector1.match(win_image1, stylesheet, document)
    assert nix_selector2.match(win_image2, stylesheet, document)
    assert win_selector1.match(nix_image1, stylesheet, document)
    assert win_selector2.match(nix_image2, stylesheet, document)
    assert win_selector1.match(win_image1, stylesheet, document)
    assert win_selector2.match(win_image2, stylesheet, document)

    assert not nix_selector1.match(nix_image2, stylesheet, document)
    assert not nix_selector2.match(nix_image1, stylesheet, document)
    assert not win_selector1.match(nix_image2, stylesheet, document)
    assert not win_selector2.match(nix_image1, stylesheet, document)


def test_select_referencingparagraph():
    paragraph = Paragraph('A paragraph with some text.', style='boxed')
    paragraph.classes.append('cls1')
    paragraph_with_id = Paragraph('A paragraph with an ID.', id='par')
    paragraph_with_id.classes.extend(['cls2', 'cls3'])
    refpar = ReferencingParagraph(paragraph)
    refpar_by_id = ReferencingParagraph('par')
    doctree = DocumentTree([paragraph, paragraph_with_id, refpar, refpar_by_id])
    document = Article(doctree)
    container = FakeContainer(document)
    document.prepare(container)
    stylesheet = document.stylesheet

    refpar_match1 = ReferencingParagraph.like(target_style='boxed')
    refpar_match2 = ReferencingParagraph.like(target_has_class='cls1')
    refpar_match3 = ReferencingParagraph.like(target_style='boxed',
                                              target_has_class='cls1')
    refpar_by_id_match = ReferencingParagraph.like(target_has_classes=['cls2', 'cls3'])
    bad_match = ReferencingParagraph.like(target_style='boxed',
                                          target_has_class='cls2')

    assert refpar_match1.match(refpar, stylesheet, document)
    assert refpar_match2.match(refpar, stylesheet, document)
    assert refpar_match3.match(refpar, stylesheet, document)
    assert refpar_by_id_match.match(refpar_by_id, stylesheet, document)

    assert not refpar_match1.match(refpar_by_id, stylesheet, document)
    assert not refpar_match2.match(refpar_by_id, stylesheet, document)
    assert not refpar_match3.match(refpar_by_id, stylesheet, document)
    assert not refpar_by_id_match.match(refpar, stylesheet, document)

    assert not bad_match.match(paragraph, stylesheet, document)
    assert not bad_match.match(paragraph_with_id, stylesheet, document)
    assert not bad_match.match(refpar, stylesheet, document)
    assert not bad_match.match(refpar_by_id, stylesheet, document)
