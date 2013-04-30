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
# $Log: definitions.py,v $
# Revision 1.1  2006/12/09 21:34:17  diedrich
# Initial commit
#
#

# WMF File structure from: http://www.fileformat.info/format/wmf/


# typedef struct _WmfSpecialHeader
# {
#   DWORD Key;           /* Magic number (always 9AC6CDD7h) */
#   WORD  Handle;        /* Metafile HANDLE number (always 0) */
#   SHORT Left;          /* Left coordinate in metafile units */
#   SHORT Top;           /* Top coordinate in metafile units */
#   SHORT Right;         /* Right coordinate in metafile units */
#   SHORT Bottom;        /* Bottom coordinate in metafile units */
#   WORD  Inch;          /* Number of metafile units per inch */
#   DWORD Reserved;      /* Reserved (always 0) */
#   WORD  Checksum;      /* Checksum value for previous 10 WORDs */
# } WMFSPECIAL;

placeable_header_fmt = "<IHhhhhHIH"


# typedef struct _WindowsMetaHeader
# {
#   WORD  FileType;       /* Type of metafile (1=memory, 2=disk) */
#   WORD  HeaderSize;     /* Size of header in WORDS (always 9) */
#   WORD  Version;        /* Version of Microsoft Windows used For example, in a metafile created by Windows 3.0, this item would have the value 300h. */
#   DWORD FileSize;       /* Total size of the metafi+le in WORDs */
#   WORD  NumOfObjects;   /* Number of objects in the file */
#   DWORD MaxRecordSize;  /* The size of largest record in WORDs */
#   WORD  NoParameters;   /* Not Used (always 0) */
# } WMFHEAD;

wmf_header_fmt = "<HHHIHIH"


# typedef struct _StandardMetaRecord
# {
#     DWORD Size;          /* Total size of the record in WORDs */
#     WORD  Function;      /* Function number (defined in WINDOWS.H) */
#     WORD  Parameters[];  /* Parameter values passed to function */
# } WMFRECORD;
start_standard_meta_record_fmt = "<IH"

# Metafile Functions: Info from the Wine Project's wingdi.h file.
metafile_functions = { 0x0201: "setbkcolor",
                       0x0102: "setbkmode",               
                       0x0103: "setmapmode",              
                       0x0104: "setrop2",                 
                       0x0105: "setrelabs",               
                       0x0106: "setpolyfillmode",         
                       0x0107: "setstretchbltmode",       
                       0x0108: "settextcharextra",        
                       0x0209: "settextcolor",            
                       0x020a: "settextjustification",    
                       0x020b: "setwindoworg",            
                       0x020c: "setwindowext",            
                       0x020d: "setviewportorg",          
                       0x020e: "setviewportext",          
                       0x020f: "offsetwindoworg",         
                       0x0410: "scalewindowext",          
                       0x0211: "offsetviewportorg",       
                       0x0412: "scaleviewportext",        
                       0x0213: "lineto",                  
                       0x0214: "moveto",                  
                       0x0415: "excludecliprect",         
                       0x0416: "intersectcliprect",       
                       0x0817: "arc",                     
                       0x0418: "ellipse",                 
                       0x0419: "floodfill",               
                       0x081a: "pie",                     
                       0x041b: "rectangle",               
                       0x061c: "roundrect",               
                       0x061d: "patblt", 
                       0x001e: "savedc", 
                       0x041f: "setpixel",                
                       0x0220: "offsetcliprgn",           
                       0x0521: "textout",                 
                       0x0922: "bitblt",                  
                       0x0b23: "stretchblt",              
                       0x0324: "polygon",                 
                       0x0325: "polyline",                
                       0x0626: "escape",                  
                       0x0127: "restoredc",               
                       0x0228: "fillregion",              
                       0x0429: "frameregion",             
                       0x012a: "invertregion",            
                       0x012b: "paintregion",             
                       0x012c: "selectclipregion",        
                       0x012d: "selectobject",            
                       0x012e: "settextalign",            
                       0x0830: "chord",                   
                       0x0231: "setmapperflags",          
                       0x0a32: "exttextout",              
                       0x0d33: "setdibtodev",             
                       0x0234: "selectpalette",           
                       0x0035: "realizepalette",          
                       0x0436: "animatepalette",          
                       0x0037: "setpalentries",           
                       0x0538: "polypolygon",             
                       0x0139: "resizepalette",           
                       0x0940: "dibbitblt",               
                       0x0b41: "dibstretchblt",           
                       0x0142: "dibcreatepatternbrush",   
                       0x0f43: "stretchdib",              
                       0x0548: "extfloodfill",            
                       0x01f0: "deleteobject",            
                       0x00f7: "createpalette",           
                       0x01f9: "createpatternbrush",      
                       0x02fa: "createpenindirect",       
                       0x02fb: "createfontindirect",      
                       0x02fc: "createbrushindirect",     
                       0x06FF: "createregion", } 

