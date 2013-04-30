#!/usr/bin/python
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log: gs.py,v $
# Revision 1.5  2006/10/16 12:52:43  diedrich
# Changed my CVS Root to Savannah, commiting changes since the upload.
#
# Revision 1.5  2006/10/14 22:25:42  t4w00-diedrich
# Massive docstring update for epydoc.
#
# Revision 1.4  2006/09/19 14:10:03  t4w00-diedrich
# All of Ghostscripts fonts are resident again. This dramatically
# dercreases jpcd preview files and increases the usefullness of the gs
# class.
#
# Revision 1.3  2006/09/06 23:24:09  t4w00-diedrich
# Resident fonts now include a file pointer to their outline files.
#
# Revision 1.2  2006/08/29 01:09:23  t4w00-diedrich
# Many things are working now and I'm to tired for the details.
#
# Revision 1.1.1.1  2006/08/16 20:58:54  t4w00-diedrich
# Initial import
#
#

"""
This module implements an psg interface for Ghostscript.
"""
import sys, os, os.path, re, warnings
from string import *
from warnings import warn
from sets import Set

from psg.exceptions import *
from interpreter import interpreter

class gs(interpreter):
    def __init__(self, executable="gs", gs_lib=[], fontmap=None):
        """
        This class will try to look at the Ghostscript executable's compiled
        in paths (by calling gs -h and looking at the 'Search Path' section)
        and at the GS_LIB environment variable.
        
        @param executable: Provide a full path for the Ghostscript executable
          (and thus which installation) you wish to use.
        @param gs_lib: List of directories containing resources. Using this
          *overwrites* the gs's internal settings and the environment!
        @param fontmap: gs's Fontmap file. If omited the first one found on
           the gs_lib path will be used.
        """
        self.executable = executable
        
        if len(gs_lib) == 0:
            # Get gs's internal paths by calling gs -h
            gs_help = os.popen("%s -h" % self.executable, "r")

            found = False
            while not found:
                line = gs_help.readline()
                if line.startswith("Search path:"): found = True

            compiled_path = ""
            while True:
                line = gs_help.readline()
                if line == "" or line[0] != " ":
                    break
                else:
                    compiled_path += line

            parts = split(compiled_path, ":")
            gs_lib = map(strip, parts)
            gs_help.close()

            # Get additional path elements from the GS_LIB environment
            # variable
            GS_LIB = os.getenv("GS_LIB", "")
            parts = split(GS_LIB, ":")
            GS_LIB = map(strip, parts)
            
            gs_lib += GS_LIB

        gs_lib = map(os.path.abspath, gs_lib)
        gs_lib = filter(os.path.exists, gs_lib)
        gs_lib = Set(gs_lib)

        interpreter.__init__(self, gs_lib, {}) # fontmap is set below
        
        # Parse the fontmap
        if fontmap is None:
            try:
                fontmap = self.open_on_path("Fontmap", "r")
            except FileNotFoundError:
                warn("Could not find Fontmap file on gs path")
                fontmap = None
        else:
            try:
                fontmap = open(fontmap, "r")
            except OSError:
                fontmap = None
                warn("Could not open Fontmap " + repr(fontmap))

        if fontmap is not None:
            try:
                fontmap = self.parse_fontmap(fontmap)
            except FontmapParseError:
                fontmap = {}
        else:
            fontmap = {}

        if fontmap == {}:
            warn("Proceeding without infomation on resident fonts (Fontmap)")
        else:
            self.fonts = fontmap

    def open_on_path(self, filename, mode="r"):
        """
        Open the first instance found for filname by find_on_path and
        return a filepointer.

        @raises FileNotFoundError: instead of OSError!
        """
        try:
            return open(self.find_on_path(filename), mode)
        except OSError:
            raise FileNotFoundError(filename + " could not be openend")
        

    def find_on_path(self, filename):
        """
        Find the first instance of filename occuring on the resource path.
        Non existing paths will be ignored. Directory and files that can
        otherwise not be read will be ignored and warned about.

        @param paths: Paths to be searched. Defaults to self.fontpath

        @returns: A file pointer
        @raises FileNotFoundError:
        """
        for path in self.fontpath:
            if os.path.exists(path):
                try:
                    files = os.listdir(path)
                    
                    if filename in files:
                        return os.path.join(path, filename)
                    
                except OSError:
                    warn("Could not read resource directory " + path)
                    continue

        raise FileNotFoundError(filename + " could not be found on the path")

    runlibfile_re = re.compile(r"\((.*?)\)\s+.runlibfile")
    fontfile_re = re.compile(r"/(.*?)\s+\((.*?)\)\s*;")
    fontalias_re = re.compile(r"/(.*?)\s+/(.*?)\s*;")

    def parse_fontmap(self, fp):
        """
        Return a font dictionary as describe for interpreter.fonts.
        """
        ret = {}
        while True:
            orig_line = fp.readline()
            if orig_line == "": break

            # Remove comments
            line = split(orig_line, "%", 1)[0]

            # And (otherwise) empty lines
            line = strip(line)            
            if line == "": continue

            # Check for "includes" (.runlibfile)
            match = self.runlibfile_re.match(line)
            if match is not None:
                filename = match.group(1)

                try:
                    include_fp = self.open_on_path(filename)
                    fontmap = self.parse_fontmap(include_fp)
                    include_fp.close()
                    ret.update(fontmap)
                except FileNotFoundError:
                    warn("Fontmap may be incomplete. Can't open %s" %\
                                                             repr(filename))
            if match is None:
                match = self.fontfile_re.match(line)
                if match is not None:
                    fontname = match.group(1)
                    filename = match.group(2)

                    try:
                        filename = self.find_on_path(filename)
                    except FileNotFoundError:
                        msg = "Ignoring %s, because %s does not exist"
                        msg = msg % ( repr(fontname), repr(filename), )
                        #warnings.warn(msg)
                        # Ignore font files that do not exist just like gs
                        # does
                        continue
                        
                    try:
                        font = self.font_from_filename(filename,
                                                       resident=True, 
                                                       lazy=True)
                        ret[fontname] = font
                    except FileNotFoundError, e:
                        warn("Can't use font %s, because %s" % ( fontname,
                                                                   str(e), ))

            if match is None:
                match = self.fontalias_re.match(line)
                if match is not None:
                    fontname = match.group(1)
                    alias = match.group(2)

                    ret[fontname] = alias

            if match is None:
                warn("Fontmap parser didn't know how to handle this line: %s"%\
                                                                 orig_line)
                    
        return ret


        
            
        
        



# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

