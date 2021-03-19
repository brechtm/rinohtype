import json

from collections.abc import Iterable
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request

from poetry.core.factory import Factory
from poetry.core.semver import parse_single_constraint as parse_version


VERSION_PARTS = ('major', 'minor', 'patch')


def get_versions(dependency: str, granularity: str = 'minor',
                 # ascending: bool = False, limit: Optional[int] = None,
                 # allow_prerelease: bool = False,
                 ) -> Iterable[str]:
    """Yield all versions of `dependency` considering version constraints

    Args:
        dependency: the name of the dependency
        granularity: yield only the newest patch version of each major/minor
            release
        ascending: count backwards from latest version, by default (not much
            use without the 'limit' arg)
        limit: maximum number of entries to return
        allow_prerelease: whether to include pre-release versions

    Yields:
        All versions of `dependency` that match the version constraints defined
        and in this project's pyproject.toml and the given `granularity`.

    """
    package = Factory().create_poetry(Path(__file__).parent).package
    for requirement in package.requires:
        if requirement.name == dependency:
            break
    else:
        raise ValueError(f"{package.name} has no dependency '{dependency}'")
    filtered_versions = [version for version in all_versions(dependency)
                         if requirement.constraint.allows(version)]
    parts = VERSION_PARTS[:VERSION_PARTS.index(granularity) + 1]
    result = {}
    for version in filtered_versions:
        key = tuple(getattr(version, part) for part in parts)
        result[key] = (max((result[key], version))
                       if key in result else version)
    return [str(version) for version in result.values()]


def all_versions(dependency):
    request = Request(f'https://pypi.org/pypi/{dependency}/json')
    response = urlopen(request)
    json_string = response.read().decode('utf8')
    json_data = json.loads(json_string)
    yield from (parse_version(version) for version in json_data['releases'])
