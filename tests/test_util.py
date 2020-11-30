# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh import register_template, register_typeface
from rinoh.font import Typeface
from rinoh.fonts.adobe14 import helvetica
from rinoh.template import DocumentTemplate


class MyTemplate(DocumentTemplate):
    pass


def test_dynamic_entry_points():
    register_template('my_template', MyTemplate)
    register_typeface('swiss', helvetica)

    assert DocumentTemplate.from_string('my_template') is MyTemplate
    assert Typeface.from_string('swiss') is helvetica


def test_dynamic_entry_point_type():
    with pytest.raises(ValueError) as exc:
        register_template('beautiful-template', 42)
    assert "is not a DocumentTemplate subclass" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        register_typeface('beautiful-typeface', None)
    assert "is not a Typeface instance" in str(exc.value)


def test_installed_entry_point_conflict():
    with pytest.raises(ValueError) as exc:
        register_template('article', MyTemplate)
    assert "distribution 'rinohtype'" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        register_typeface('helvetica', helvetica)
    assert "distribution 'rinohtype'" in str(exc.value)


def test_dynamic_entry_point_conflict():
    register_template('another_template', MyTemplate)
    with pytest.raises(ValueError) as exc:
        register_template('another_template', MyTemplate)
    assert "using 'register_template" in str(exc.value)

    register_typeface('another_typeface', helvetica)
    with pytest.raises(ValueError) as exc:
        register_typeface('another_typeface', helvetica)
    assert "using 'register_typeface" in str(exc.value)
