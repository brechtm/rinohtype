# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import json

from itertools import chain
from pathlib import Path
from shutil import unpack_archive
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from appdirs import AppDirs

from rinoh.font import Typeface
from rinoh.font.opentype import OpenTypeFont


__all__ = ['google_fonts']


DOWNLOAD_URL = 'https://fonts.google.com/download?family={}'

APPDIRS = AppDirs("rinohtype", "opqode")
USER_DATA_DIR = Path(APPDIRS.user_data_dir)
USER_CACHE_DIR = Path(APPDIRS.user_cache_dir)

DOWNLOAD_PATH = USER_CACHE_DIR / 'google_fonts'
STORAGE_PATH = USER_DATA_DIR / 'google_fonts'
MANIFEST_PATH = STORAGE_PATH / 'fonts.json'


GOOGLE_TYPEFACES = {}


def google_typeface(name):
    try:
        typeface = GOOGLE_TYPEFACES[name]
    except KeyError:
        fonts = google_fonts(name)
        GOOGLE_TYPEFACES[name] = typeface = Typeface(name, *fonts)
    return typeface


def google_fonts(name):
    lc_name = name.lower()
    if lc_name.endswith('condensed') or lc_name.endswith('extended'):
        raise Exception

    manifest = Manifest(MANIFEST_PATH)
    if name not in manifest:
        print("Looking for typeface '{}' on Google Fonts".format(name))
        manifest_record = manifest[name] = {}
        for fonts_name in font_widths(name):
            fonts_path = STORAGE_PATH / fonts_name
            if try_install_family(fonts_name, fonts_path):
                manifest_record[fonts_name] = None
        if not manifest_record:
            raise GoogleFontNotFound(name)
        manifest.save()
    paths = [STORAGE_PATH / fonts_name for fonts_name in manifest[name]]
    return [OpenTypeFont(font_path) for path in paths
            for font_path in find_static_font_files(path)]


def font_widths(name):
    for var in chain([''], (a + b for b in (' Condensed', ' Expanded')
                            for a in (' Semi', '', ' Extra', ' Ultra'))):
        yield name + var


class GoogleFontNotFound(Exception):
    def __init__(self, typeface_name):
        self.typeface_name = typeface_name


# TODO: add font version/last-checked field
class Manifest(dict):
    VERSION = 1
    VERSION_KEY = '_manifest_version'

    def __init__(self, file_path):
        self.file_path = file_path
        if self.file_path.exists():
            with open(MANIFEST_PATH) as f:
                self.update(json.load(f))
            if self[self.VERSION_KEY] != self.VERSION:
                raise NotImplementedError
            del self[self.VERSION_KEY]

    def save(self):
        self[self.VERSION_KEY] = self.VERSION
        with open(self.file_path, 'w') as f:
            json.dump(self, f)


def installed_google_fonts_typefaces():
    manifest = Manifest(MANIFEST_PATH)
    for name in manifest:
        yield google_typeface(name)


def find_static_font_files(path):
    static = path / 'static'
    path = static if static.is_dir() else path
    yield from path.glob('*.ttf')


def try_install_family(name, family_path):
    download_url = DOWNLOAD_URL.format(quote(name))
    download_path = download_file(name, download_url)
    if download_path:
        print(" unpacking...", end='')
        family_path.mkdir(parents=True, exist_ok=True)
        unpack_archive(download_path, family_path)
        print(" done")
        return True


def download_file(name, url):
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(url) as response:
            print("Found '{}': downloading...".format(name), end='')
            filename = response.headers.get_filename()
            download_path = DOWNLOAD_PATH / filename
            with download_path.open('wb') as f:
                while True:
                    buffer = response.read(8192)
                    if not buffer:
                        break
                    f.write(buffer)
    except HTTPError as e:
        if e.code == 404:
            return None     # not found
        raise
    return download_path
