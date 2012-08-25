
import ctypes

from .parse import grab, calculate_checksum, decode, PLATFORM_WINDOWS
from .parse import byte, ushort, array, short
from .tables import HEAD, HHEA, MAXP, OS_2, POST, NAME, NAME_RECORD
from .tables import LANG_TAG_RECORD, CMAP, CMAP_RECORD, CMAP_4
from .. import Font
from ..style import MEDIUM, UPRIGHT, NORMAL, ITALIC


class OpenTypeFont(Font, dict):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.metrics = None
        self.encoding = None
        super().__init__(weight, slant, width)
        file = open(filename, 'rb')
        self.parse_tables(file)
        file.close()
        # TODO: extract data from tables
##        self.metrics = FontMetrics()
##        for glyph in ...:
##            glyph_metrics = GlyphMetrics(None?, width, bounding_box, code)
##            self.metrics.glyphs[glyph_metrics.code] = glyph_metrics
        # TODO: self.metrics.kerning_pairs
        # TODO: self.metrics.ligatures

    def parse_tables(self, file):
        tup = grab(file, '4sHHHH')
        version, num_tables, search_range, entry_selector, range_shift = tup
        tables = {}
        for i in range(num_tables):
            tag, checksum, offset, length = grab(file, '4sLLL')
            tables[tag.decode('ascii')] = offset, length, checksum
        for tag, (offset, length, checksum) in tables.items():
            cs = calculate_checksum(file, offset, length, tag=='head')
            assert cs == checksum
        self.head = self.parse_table(HEAD, file, tables['head'][0])
        self.post = self.parse_table(POST, file, tables['post'][0])
        if self.post['version'] != 3.0:
            raise NotImplementedError()
        self.hhea = self.parse_table(HHEA, file, tables['hhea'][0])
        self.maxp = self.parse_maxp(file, tables['maxp'][0])
        self.hmtx = self.parse_hmtx(file, tables['hmtx'][0],
                                    self.hhea['numberOfHMetrics'],
                                    self.maxp['numGlyphs'])
        self.os_2 = self.parse_table(OS_2, file, tables['OS/2'][0])
        self.name = self.parse_name(file, tables['name'][0])
        self.cmap = self.parse_cmap(file, tables['cmap'][0])

    def parse_table(self, table, file, offset):
        out = {}
        file.seek(offset)
        for key, reader in table:
            value = reader(file)
            if key is not None:
                out[key] = value
        return out

    def parse_maxp(self, file, offset):
        out = {}
        file.seek(offset)
        for i, (key, reader) in enumerate(MAXP):
            if key == 'maxPoints' and out['version'] != 1.0:
                break
            out[key] = reader(file)
        return out

    def parse_hmtx(self, file, offset, number_of_h_metrics, num_glyphs):
        out = []
        file.seek(offset)
        for i in range(number_of_h_metrics):
            advance_width, left_side_bearing = grab(file, 'Hh')
            out.append((advance_width, left_side_bearing))
        for i in range(num_glyphs - number_of_h_metrics):
            left_side_bearing, = grab(file, 'h')
            out.append((advance_width, left_side_bearing))
        return out

    def parse_name(self, file, offset):
        table = self.parse_table(NAME, file, offset)
        records = []
        for i in range(table['count']):
            record = self.parse_table(NAME_RECORD, file, file.tell())
            records.append(record)
        if table['format'] == 1:
            raise NotImplementedError
        data_offset = file.tell()
        out = {}
        for record in records:
            file.seek(data_offset + record['offset'])
            data = file.read(record['length'])
            # TODO: decode according to platform and encoding
            if record['platformID'] == PLATFORM_WINDOWS:
                out[record['nameID']] = decode(record['platformID'],
                                               record['encodingID'], data)
        return out

    def parse_cmap(self, file, offset):
        table = self.parse_table(CMAP, file, offset)
        records = []
        for i in range(table['numTables']):
            record = self.parse_table(CMAP_RECORD, file, file.tell())
            records.append(record)
        for record in records:
            record_offset = offset + record['offset']
            file.seek(record_offset)
            table_format = ushort(file)
            if table_format in (8, 10, 12, 13):
                reserved = ushort(file)
            length = ushort(file)
            if table_format != 14:
                language = ushort(file),
            # TODO: detect already-parsed table
            if table_format == 0: # byte encoding table
                out = {zip(range(256), array(byte, 256))(file)}
            elif table_format == 2: # high-byte mapping through table
                raise NotImplementedError
            elif table_format == 4: # segment mapping to delta values
                meta = self.parse_table(CMAP_4, file, file.tell())
                seg_count = meta['segCountX2'] >> 1
                end_count = array(ushort, seg_count)(file)
                reserved_pad = ushort(file)
                start_count = array(ushort, seg_count)(file)
                id_delta = array(short, seg_count)(file)
                id_range_offset = array(ushort, seg_count)(file)
                glyph_id_array_length = (record_offset + length - file.tell())
                glyph_id_array = array(ushort, glyph_id_array_length >> 1)(file)
                segments = zip(start_count, end_count, id_delta,
                               id_range_offset)
                out = {}
                for i, (start, end, delta, range_offset) in enumerate(segments):
                    if i == seg_count - 1:
                        assert end == 0xFFFF
                        break
                    if range_offset > 0:
                        for j, code in enumerate(range(start, end + 1)):
                            index = (range_offset >> 1) - seg_count + i + j
                            out[code] = glyph_id_array[index]
                    else:
                        for code in range(start, end + 1):
                            out[code] = (code + delta) % 2**16
            elif table_format == 6: # trimmed table mapping
                first_code, entry_count = ushort(file), ushort(file)
                out = {code: index for code, index in
                       zip(range(first_code, first_code + entry_count),
                           array(ushort, entry_count)(file))}
            else:
                raise NotImplementedError('table format {}', table_format)
            record['map'] = out
        table['records'] = records
        return table


##class CMapTable(object):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
##
##
##class CMapTable4(CMapTable):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
