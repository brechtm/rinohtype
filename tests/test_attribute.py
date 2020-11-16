import pytest
from rinoh.attribute import Attribute, Bool
from rinoh.style import Style


class MockStyle(Style):

    boolean = Attribute(Bool, True, "A boolean attribute")


def test_attribute_default():
    style = MockStyle()
    assert(style.boolean == True)


def test_attribute_non_default():
    style = MockStyle(boolean=False)
    assert(style.boolean == False)


def test_attribute_from_class():
    attribute = MockStyle.boolean
    assert(attribute.name == "boolean")
    assert(attribute.description == "A boolean attribute")
    assert(attribute.accepted_type == Bool)
    assert(attribute.default_value == True)

def test_attribute_wrong_type():
    style = MockStyle()
    with pytest.raises(TypeError):
        style.boolean = None