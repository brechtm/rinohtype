# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import json
import sys

from pathlib import Path
from shutil import unpack_archive
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from appdirs import AppDirs

from rinoh.font import Typeface
from rinoh.font.opentype import OpenTypeFont


__all__ = ['google_fonts']


LIST_URL = 'https://fonts.google.com/download/list?family={}'

APPDIRS = AppDirs("rinohtype", "opqode")
STORAGE_PATH = Path(APPDIRS.user_data_dir) / 'google_fonts'
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


GOOGLE_TYPEFACES = {}


def google_typeface(name):
    try:
        typeface = GOOGLE_TYPEFACES[name]
    except KeyError:
        fonts = google_fonts(name)
        GOOGLE_TYPEFACES[name] = typeface = Typeface(name, *fonts)
    return typeface


def google_fonts(name):
    for item in STORAGE_PATH.iterdir():
        if item.is_dir() and item.name == name:
            fonts_path = item
            break
    else:
        fonts_path = STORAGE_PATH / name
        sys.stdout.write("\r"); sys.stdout.flush()  # clear progress indicator
        print("Typeface '{}' is not installed; searching Google Fonts."
              .format(name))
        if not try_install_family(name, fonts_path):
            raise GoogleFontNotFound(name)
    return [OpenTypeFont(font_path)
            for font_path in find_static_font_files(fonts_path)]


class GoogleFontNotFound(Exception):
    def __init__(self, typeface_name):
        self.typeface_name = typeface_name


def installed_google_fonts_typefaces():
    for item in STORAGE_PATH.iterdir():
        if item.is_dir():
            yield google_typeface(item.name)


def find_static_font_files(path):
    static = path / 'static'
    path = static if static.is_dir() else path
    yield from path.glob('**/*.ttf')
    yield from path.glob('**/*.otf')


def try_install_family(name, family_path):
    list_url = LIST_URL.format(quote(name))
    try:
        family = json.loads(bytearray(urlopen(list_url).read())[5:])
    except HTTPError as e:
        if e.code == 400:
            print("-> not found: please check the typeface name (case-sensitive!)")
            return False
        raise NotImplementedError
    family_path.mkdir(parents=True, exist_ok=True)
    for entry in family['manifest']['files']:
        destination_path = family_path / entry['filename']
        destination_path.write_text(entry['contents'])
    for entry in family['manifest']['fileRefs']:
        file_path = entry['filename']
        download_path = family_path / file_path
        download_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"-> downloading {file_path}")
        download_file(file_path, entry['url'], family_path)
    return True


def download_file(filename, url, destination):
    try:
        with urlopen(url) as response:
            download_path = Path(destination) / filename
            with download_path.open('wb') as f:
                while True:
                    buffer = response.read(8192)
                    if not buffer:
                        break
                    f.write(buffer)
    except HTTPError as e:
        if e.code in (404, 403):
            return None     # not found
        raise
    return download_path
