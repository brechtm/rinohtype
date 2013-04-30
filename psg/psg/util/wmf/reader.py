#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
# $Log: reader.py,v $
# Revision 1.3  2006/12/10 22:52:28  diedrich
# Did some more work on the PostScript reader, testing.
#
# Revision 1.2  2006/12/10 01:11:15  diedrich
# Bugfixing
#
# Revision 1.1  2006/12/09 21:34:17  diedrich
# Initial commit
#
#

import sys, struct
from string import *
from types import *
from warnings import warn
from copy import deepcopy

from definitions import *
from wmfutil import *

try:
    from psg.debug import debug
except ImportError:
    debug = sys.stderr

class box:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top

class wmf_reader:

    # Initialization
    def __init__(self, fp):
        """
        @param fp: Input wmf file pointer. Opened for reading; it does
           not need to be seekable. 
        """
        self.stream = struct_stream(fp)


        # Is this a placeable WMF file?
        ( Key, Handle, Left, Top, Right, Bottom, Inch,
          Reserved, Checksum, ) = self.stream.read_fmt(placeable_header_fmt)

        if Key == 0x9AC6CDD7:
            self.bounding_box = box(Left, Top, Right, Bottom)
            self.resolution = Inch
        else:
            self.get_placing_info()

        # Read the actual WMF header
        tpl = self.stream.read_fmt(wmf_header_fmt)
        ( FileType, HeaderSize, Version, FileSize, NumOfObjects, MaxRecordSize,
          dummy, ) = tpl

        if HeaderSize != 9:
            raise IOError("This does not seem to be a WMF file at all!")

        self.creator_os_version = Version

        # Relevant internal data structured
        self.dc_stack = []
        self.current_dc = self._dc(self)
        self.object_list = self._object_list()

    def get_placing_info(self):
        """
        This method is called in case the WMF file did not contain
        information on its size and resolution (it is not a
        'placeable' meta file. There is not default implementation,
        non-placeable meta files will yield an NotImplementedError
        with a nice error message.

        Any implementation of this method must set its object's
        bounding_box and resolution attribute.
        """
        raise NotImplementedError("This implementation of a wmf_reader "
                                  "cannot handle non-placeable WMF files.")


    # Methods that do the actual reading

    def function_objects(self):
        """
        A generator yielding _function_cls instances for each of the
        metafile records in the input wmf file.
        """
        while True:            
            size, function_no = self.stream.read_fmt(
                start_standard_meta_record_fmt)
            
            if function_no == 0:
                # A function# 0 indicates the end of the meta file.
                break
            else:
                function_name = metafile_functions.get(function_no, None)
                print >> debug, "function_name\033[1;2m", function_name, "\033[1;0m"
                
                if function_name is None:
                    #warn("Unknown WMF function number: %i" % function_no)
                    function_name = "None"
                    
                function_cls = getattr(self, function_name, None)
                #if function_cls is not None:
                    #warn(("WMF file function not implemented "
                    #      "by this reader: %s") % repr(function_name))
                    
                if function_cls is None:
                    # We don't know which function this function# belongs to
                    # or this particular function has not been implemented by
                    # this reader. We just skip the parameters to that function
                    # and turn to the next.

                    # The size parameter is in 16bit WORDS, so multiply by 2,
                    # but it also contains a DWORD and a WORD already read, so
                    # substract 6.
                    self.stream.skip( (size * 2) - 6 )
                else:
                    yield function_cls(self, size)


    def save(self, fp):
        """
        The save() method creates a result_object and then 'plays
        back' the wmf file into the result_object while reading the
        function descriptions one after the other. Save()'s parameter
        list may need updating to match your result_object class'
        constructor. I put fp here as a reasonable default...

        @param fp: Output file pointer, opened for writing.
        """
        output_object = self._output(self, fp)
        
        for a in self.function_objects():
            a.playback(output_object)

        output_object.finish()


    # Result class

    class _output:
        """
        Model the output container for the reading and conversion
        process' result. The default implementation simply stores
        a file pointer which is closed on finish().
        """
        def __init__(self, reader, fp):
            self.reader = reader
            self.fp = fp

        def finish(self):
            """
            The finish() method is called after the last meta record
            has been 'played back'.
            """
            self.fp.close()

    # Internal WMF data structures.
    class _object_list(list):
        """
        An append to this kind of list will put the new object to the
        first free position on it (marked by a None value).
        """
        def append(self, obj):
            for idx, a in enumerate(self):
                if a is None:
                    self[idx] = obj
                    return

            list.append(self, obj)

    class _select_object:
        """
        Common base class for drawing tools.

        These select_objects (or drawing tools) have three methods:
        create, select and destroy, that get called whenever a pen or
        brush or so is created, selected into the current dc or
        destroyed. The default implementations do nothing.
        """
        def create(self, output_object):
            pass

        def select(self, output_object):
            pass

        def destroy(self, output_object):
            pass

    class _pen(_select_object):
        """
        @ivar style: String, one of the styles below.
        @ivar width: Pair of integers representing the width. (Why
           this is a pair exceeds my imagination).
        @ivar color: Three tuple representing RGB color.
        @ivar endcap: String indicating how the ends of lines are to
           be drawn.
        @ivar join: String indicating how the joins of lines are to be
           drawn.
        """
        styles = { 0: "solid",
                   1: "dash",          # ------- 
                   2: "dot",           # ....... 
                   3: "dashdot",       # _._._._ 
                   4: "dashdotdot",    # _.._.._ 
                   5: "null",
                   6: "insideframe",
                   7: "userstyle",
                   8: "alternate", }

        style_mask = 0x0000000F

        endcaps = { 0x00000000: "round",  
                    0x00000100: "square", 
                    0x00000200: "flat",   
                    0x00000F00: "mask", }
        
        endcap_mask = 0x00000F00

        joins = { 0x00000000: "round",
                  0x00001000: "bevel",
                  0x00002000: "miter",
                  0x0000F000: "mask", }
        
        join_mask = 0x0000F000        
        
        
        def __init__(self, style="null", width=(0,0,), color=(0,0,0),
                     endcap="round", join="round"):
            
            if type(style) == IntType:
                no = style & self.endcap_mask
                endcap = self.endcaps[no]

                no = style & self.join_mask
                join = self.joins[no]
    
                no = style & self.style_mask
                style = self.styles[no]

            self.style = style
            self.width = width
            self.color = color
            self.endcap = endcap
            self.join = join

                
    class _brush(_select_object):
        """
        @ivar style: String, one of styles, see below.
        @ivar color: Three tuple representing RGB color.
        @ivar hatch: Integer representing one of the wingdi.h constants (HS_*)
        """
        styles = { 0: "solid", 1: "null", 2: "hatched", }
        def __init__(self, style="null", color=(0,0,0), hatch=None):
            if type(style) != StringType:
                style = self.styles[int(style)]
            else:                
                if lower(style) not in self.styles.values():
                    raise ValueError("Style must be one of %s" % repr(styles))
                                 
            self.style = lower(style)
            self.color = color
            self.hatch = hatch

    class _font(_select_object):
        pass

    class _clip_region(_select_object):
        pass

    class _pal(_select_object):
        pass

    class _dc:
        """
        Model a 'Drawing Context'.
        """
        def __init__(self, reader,
                     brush=None, pen=None, font=None,
                     textcolor=(0,0,0), bgcolor=(255,255,255),
                     textalign=0, bgmode="transparent",
                     polyfillmode="alternate",
                     charextra=0, breakextra=0, ROPmode="copypen",
                     clip_region=None, mapmode="text"):
            
            self.reader = reader

            if brush is None:
                self.brush = reader._brush()
            else:
                self.brush = brush

            if pen is None:
                self.pen = reader._pen()
            else:
                self.pen = pen

            if font is None:
                self.font = reader._font()
            else:
                self.font = font
                
            self.textcolor = textcolor
            self.bgcolor = bgcolor
            self.textalign = textalign
            self.bgmode = bgmode
            self.polyfillmode = polyfillmode
            self.charextra = 0
            self.breakextra = 0
            self.ROPmode = ROPmode
            self.clip_region = clip_region
            self.mapmode = mapmode

        def select_object(self, idx, output_object):
            """
            This selects the selectable_object from the object_list
            pointed to by idx into this dc. The type of object is
            determined by its class name (pen, brush, font, etc)
            """
            obj = self.reader.object_list[idx]
            name = obj.__class__.__name__[1:] # remove the _
            setattr(self, name, obj)

            print >> debug,"   selected", name, "#%i" % idx

            obj.select(output_object)



    # Function base classes

    class _meta_function:
        """
        Model a function that can be stored for 'playback' in a meta
        file. 
        """
        def __init__(self, reader, size):
            """
            @param reader: The wmf_reader we belong to (an object,
               not a class).
            @param size: The size attribute of our meta record.   
            """
            self.reader = reader
            self.size = size

        def playback(self, output_object):
            """
            The playback() method is called by reader.save(). Its job
            is to retrieve informatin from the wmf file that belongs
            to this meta function and pass it to the draw() method
            which is called with the output_object and the retrieved
            information as parameters.

            The default implementation does nothing but call draw()
            which, by default, raises NotImplementedError().
            """
            self.draw(output_object)

        def draw(self, output_object, *args):
            """
            The draw method does <i>something</i> with the output
            object to actually draw what's to be drawn. Or it modifies
            the state of the reader object through one of its methods
            to emulate a DeviceContext... etc.

            The default implementation raises NotImplementedError().
            """
            raise NotImplementedError()


    class _normal_function(_meta_function):
        """
        This is the base class for all those _meta_function classes
        representing meta functions with 'normal' parameter
        processing, i.e. one depending on an argument list to be
        determined by their function number's low byte. Those 16-bit
        WORDs will be read by the playback() method and then passed as
        positive integers to draw().
        """
        def playback(self, output_object):
            """
            This method goes three steps:

               - Determine the number of arguments the meta function has
               - Read that many 16bit Words from the Meta file
               - Call draw() with those words (converted to ints) as arguments
               
            """
            number_of_args = self.size - 3 # 3 -> The size field + the func #

            if number_of_args > 0:
                format_str = "<%ih" % number_of_args
                args = self.reader.stream.read_fmt(format_str)
                args = list(args)
            else:
                args = ()

            print >> debug,"  ",
            for a in args: print >> debug,a,
            print >> debug, ""
            
            self.draw(output_object, *args)
            

    # Generic Function Classes (Those that usually will not need
    # overloading).
    
    class createbrushindirect(_normal_function):
        def draw(self, output_object, style, color_low, color_hi, hatch):
            color = getcolor(color_low, color_hi)
            brush = self.reader._brush(style, color, hatch)
            self.reader.object_list.append(brush)
            brush.create(output_object)

    class createpenindirect(_normal_function):
        def draw(self, output_object, style,
                 width_x, width_y,
                 color_one, color_two, *args):
            color = getcolor(color_one, color_two)
            pen = self.reader._pen(style, ( width_x, width_y, ), color)
            self.reader.object_list.append(pen)
            pen.create(output_object)

    class createfontindirect(_normal_function):
        def draw(self, output_object, *args):
            font = self.reader._font()
            self.reader.object_list.append(font)
            font.create(output_object)
            
    class selectobject(_normal_function):
        def draw(self, output_object, object_idx):
            self.reader.current_dc.select_object(object_idx, output_object)
            
    class deleteobject(_normal_function):
        def draw(self, output_object, object_idx):
            pen = self.reader.object_list[object_idx]
            pen.destroy(output_object)
            self.reader.object_list[object_idx] = None

    class setpolyfillmode(_normal_function):
        def draw(self, output_object, mode, dummy=0):
            if mode == 1:
                self.reader.current_dc.polyfillmode = "alternate"
            else:
                self.reader.current_dc.polyfillmode = "winding"
                
    class setmapmode(_normal_function):
        mapmodes = { 1: "text",
                     2: "lometric",         
                     3: "himetric",         
                     4: "loenglish",        
                     5: "hienglish",        
                     6: "twips",            
                     7: "isotropic",        
                     8: "anisotropic", }
        
        def draw(self, output_object, mode):
            self.reader.current_dc.mapmode = self.mapmodes[mode]
            
    class settextalign(_normal_function):
        def draw(self, output_object, magic):
            self.reader.current_dc.textalign = magic

    class savedc(_normal_function):
        def draw(self, output_object):
            self.reader.dc_stack.append(deepcopy(self.reader.current_dc))

    class restoredc(_normal_function):
        def draw(self, output_object, count=1):
            for a in range(count):
                self.reader.current_dc = self.reader.dc_stack.pop()

    class settextcolor(_normal_function):
        def draw(self, output_object, color_one, color_two):
            self.reader.current_dc.textcolor = getcolor(color_one, color_two)

    class settextcharextra(_normal_function):
        def draw(self, output_object, extra):
            self.reader.current_dc.charextra = extra

    
