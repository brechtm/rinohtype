# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import string
from warnings import warn
from xmlrpc.client import ServerProxy

import pip
import pkg_resources
from pkg_resources import iter_entry_points

from .util import NotImplementedAttribute, class_property
from .attribute import AttributeType


__all__ = ['Resource', 'ResourceNotInstalled']


class Resource(AttributeType):
    resource_type = NotImplementedAttribute()

    @class_property
    def entry_point_group_name(cls):
        return 'rinoh.{}s'.format(cls.resource_type)

    @classmethod
    def parse_string(cls, resource_name):
        entry_point_name = resource_name.lower()
        entry_points = iter_entry_points(cls.entry_point_group_name,
                                         entry_point_name)
        try:
            entry_point = next(entry_points)
        except StopIteration:
            raise ResourceNotInstalled(cls, resource_name, entry_point_name)
        other_distributions = [repr(ep.dist) for ep in entry_points]
        if other_distributions:
            warn("The {} '{}' is also provided by:\n".format(cls.resource_type,
                                                             resource_name)
                 + ''.join('* {}\n'.format(dist)
                           for dist in other_distributions)
                 + 'Using ' + repr(entry_point.dist))
        return entry_point.load()

    @class_property
    def installed_resources(cls):
        for entry_point in iter_entry_points(cls.entry_point_group_name):
            yield entry_point.name, entry_point

    @classmethod
    def install_from_pypi(cls, entry_point_name):
        success = False
        pypi = ServerProxy('https://pypi.python.org/pypi')
        resource_id = entry_point_name_to_identifier(entry_point_name)
        distribution_name_parts = ['rinoh', cls.resource_type, resource_id]
        for pkg in pypi.search(dict(name=distribution_name_parts)):
            if pkg['name'] == '-'.join(distribution_name_parts):
                package_name = pkg['name']
                print("Installing {} package '{}' using pip..."
                      .format(cls.resource_type, package_name))
                pip.main(['install', package_name])
                pkg_resources.working_set.__init__()  # rescan entry points
                success = True
                break
        return success


class ResourceNotInstalled(Exception):
    """Exceptions raised when a resource identified by `entry_point_name` was
    not found."""
    def __init__(self, resource_type, resource_name, entry_point_name):
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.entry_point_name = entry_point_name


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
