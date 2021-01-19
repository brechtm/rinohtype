# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

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


DOWNLOAD_URL = 'https://fonts.google.com/download?family={}'

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
    yield from path.glob('*.ttf')


def try_install_family(name, family_path):
    download_url = DOWNLOAD_URL.format(quote(name))
    download_path = download_file(name, download_url)
    if download_path:
        print(" unpacking...", end='')
        family_path.mkdir(parents=True, exist_ok=True)
        unpack_archive(str(download_path), str(family_path))
        print(" done!")
        return True
    print("-> not found: please check the typeface name (case-sensitive!)")


download_dir = None


def download_file(name, url):
    global download_dir
    if not download_dir:
        download_dir = TemporaryDirectory(prefix='rinohtype_')
    try:
        with urlopen(url) as response:
            print("-> success: downloading...".format(name), end='')
            filename = response.headers.get_filename()
            download_path = Path(download_dir.name) / filename
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
