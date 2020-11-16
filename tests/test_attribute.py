# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Alex Fargus.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.attribute import Attribute, Bool
from rinoh.style import Style


class MockStyle(Style):

    boolean = Attribute(Bool, True, "A boolean attribute")


def test_attribute_default():
    style = MockStyle()
    assert style.boolean is True


def test_attribute_non_default():
    style = MockStyle(boolean=False)
    assert style.boolean is False


def test_attribute_from_class():
    attribute = MockStyle.boolean
    assert attribute.name == "boolean"
    assert attribute.description == "A boolean attribute"
    assert attribute.accepted_type == Bool
    assert attribute.default_value is True


def test_attribute_wrong_type():
    style = MockStyle()
    with pytest.raises(TypeError):
        style.boolean = None
