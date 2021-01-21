# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import string
import sys

from collections import namedtuple
from subprocess import Popen, PIPE

try:
    from importlib import metadata as ilm
except ImportError:     # Python < 3.8
    import importlib_metadata as ilm
from warnings import warn

from .attribute import AttributeType
from .util import NotImplementedAttribute, class_property


__all__ = ['Resource', 'ResourceNotFound', 'find_entry_points']


class Resource(AttributeType):
    resource_type = NotImplementedAttribute()

    @class_property
    def entry_point_group(cls):
        return 'rinoh.{}s'.format(cls.resource_type)

    @classmethod
    def parse_string(cls, resource_name, source):
        entry_point_name = resource_name.lower()
        entry_points = find_entry_points(cls.entry_point_group,
                                         entry_point_name)
        try:
            entry_point, dist = next(entry_points)
        except StopIteration:
            raise ResourceNotFound(cls, resource_name, entry_point_name)
        other_distributions = [dist for _, dist in entry_points]
        if other_distributions:
            warn("The {} '{}' is also provided by:\n".format(cls.resource_type,
                                                             resource_name)
                 + ''.join('* {}\n'.format(dist.metadata['Name'])
                           for dist in other_distributions)
                 + "Using the one from '{}'".format(dist.metadata['Name']))
        return entry_point.load()

    @class_property
    def installed_resources(cls):
        for entry_point in ilm.entry_points()[cls.entry_point_group]:
            yield entry_point.name, entry_point

    @classmethod
    def install_from_pypi(cls, entry_point_name):
        resource_id = entry_point_name_to_identifier(entry_point_name)
        package_name = '-'.join(['rinoh', cls.resource_type, resource_id])
        pip = Popen([sys.executable, '-m', 'pip', 'install', package_name],
                    stdout=PIPE, universal_newlines=True)
        for line in pip.stdout:
            if not line.startswith('Requirement already satisfied'):
                sys.stdout.write(line)
        return pip.wait() == 0


class ResourceNotFound(Exception):
    """Exception raised when a resource was not found

    Args:
        resource_type (type): the type of the resource
        resource_name (str): the name of the resource
        entry_point_name (str): the entry point name for the resource

    """
    def __init__(self, resource_class, resource_name, entry_point_name):
        self.resource_class = resource_class
        self.resource_name = resource_name
        self.entry_point_name = entry_point_name

    @property
    def resource_type(self):
        return self.resource_class.resource_type


def entry_point_name_to_identifier(entry_point_name):
    """Transform an entry point name into an identifier suitable for inclusion
    in a PyPI package name."""
    try:
        entry_point_name.encode('ascii')
        ascii_name = entry_point_name
    except UnicodeEncodeError:
        ascii_name = entry_point_name.encode('punycode').decode('ascii')
    return ''.join(char for char in ascii_name
                   if char in string.ascii_lowercase + string.digits)


def find_entry_points(group, name=None):
    """Find all entry points with in `group`, optionally filtered by `name`

    Yields:
        (EntryPoint, Distribution): entry point and distribution it belongs to

    """
    yield from ((ep, dist) for dist in ilm.distributions()
                for ep in dist.entry_points
                if ep.group == group and (name is None or ep.name == name))


# dynamic entry point creation

GROUPS = ('rinoh.templates', 'rinoh.typefaces')

_installed_entry_points = {(ep.group, ep.name): dist
                           for dist in ilm.distributions()
                           for ep in dist.entry_points
                           if ep.group in GROUPS}


DynamicEntryPointBase = namedtuple('DynamicEntryPointBase', 'name value group')


class DynamicEntryPoint(DynamicEntryPointBase):
    """An entry point defined by value instead of by module:attribute"""

    def load(self):
        return self.value


class DynamicRinohDistribution(ilm.Distribution):
    """Distribution for registering resource entry points to at runtime"""

    def __init__(self):
        self._templates = {}
        self._typefaces = {}

    def register_template(self, name, template_class):
        """Register a template by (entry point) name at runtime"""
        self._check_existing_entry_point('template', name)
        try:
            assert issubclass(template_class, DocumentTemplate)
        except (TypeError, AssertionError):
            raise ValueError("The template '{}' you are trying to register "
                             "is not a DocumentTemplate subclass".format(name))
        self._templates[name] = template_class

    def register_typeface(self, name, typeface):
        """Register a typeface by (entry point) name at runtime"""
        self._check_existing_entry_point('typeface', name)
        if not isinstance(typeface, Typeface):
            raise ValueError("The typeface '{}' you are trying to register "
                             "is not a Typeface instance".format(name))
        self._typefaces[name] = typeface

    def _check_existing_entry_point(self, resource_type, name):
        group = 'rinoh.{}s'.format(resource_type)
        try:
            dist = _installed_entry_points[(group, name)]
            existing = "by the distribution '{}'".format(dist.metadata['Name'])
        except KeyError:
            if name in self._entry_point_groups[group]:
                existing = "using 'register_{}'".format(resource_type)
            else:
                return
        raise ValueError("A {} named '{}' has already been registered {}"
                         .format(resource_type, name, existing))

    @property
    def _entry_point_groups(self):
        return {
            'rinoh.templates': self._templates,
            'rinoh.typefaces': self._typefaces,
        }

    @property
    def entry_points(self):
        return [DynamicEntryPoint(name, value, group)
                for group, entry_points in self._entry_point_groups.items()
                for name, value in entry_points.items()]


_DISTRIBUTION = DynamicRinohDistribution()


class DynamicDistributionFinder(ilm.DistributionFinder):
    """Makes the dynamic rinohtype distribution discoverable"""

    @classmethod
    def find_distributions(cls, context=ilm.DistributionFinder.Context()):
        if context.name and context.name != 'rinohtype.dynamic':
            return
        yield _DISTRIBUTION

    @classmethod
    def find_module(cls, fullname, path=None):
        return None


sys.meta_path.append(DynamicDistributionFinder)


from .font import Typeface
from .template import DocumentTemplate
