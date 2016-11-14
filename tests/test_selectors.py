# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.image import Image


def test_image():
    nix_image1 = Image('dir/image.png')
    nix_image2 = Image('dir/subdir/image.png')
    win_image1 = Image(r'dir\image.png')
    win_image2 = Image(r'dir\subdir\image.png')
    nix_selector1 = Image.like(filename='dir/image.png')
    nix_selector2 = Image.like(filename='dir/subdir/image.png')
    win_selector1 = Image.like(filename=r'dir\image.png')
    win_selector2 = Image.like(filename=r'dir\subdir\image.png')
    assert nix_selector1.match(nix_image1, None)
    assert nix_selector2.match(nix_image2, None)
    assert nix_selector1.match(win_image1, None)
    assert nix_selector2.match(win_image2, None)
    assert win_selector1.match(nix_image1, None)
    assert win_selector2.match(nix_image2, None)
    assert win_selector1.match(win_image1, None)
    assert win_selector2.match(win_image2, None)

    assert not nix_selector1.match(nix_image2, None)
    assert not nix_selector2.match(nix_image1, None)
    assert not win_selector1.match(nix_image2, None)
    assert not win_selector2.match(nix_image1, None)
