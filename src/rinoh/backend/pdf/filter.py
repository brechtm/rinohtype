# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct, zlib

from binascii import hexlify, unhexlify
from math import ceil
from string import whitespace
from struct import pack, unpack

from ...util import consumer, class_property
from .util import FIFOBuffer


class Filter(object):
    params_class = None

    def __init__(self, params=None):
        if self.params_class is None:
            assert not params
        self.params = params

    @class_property
    def name(cls):
        return Name(cls.__name__)

    def encoder(self, destination, **kwargs):
        raise NotImplementedError

    def decoder(self, source, **kwargs):
        raise NotImplementedError


class Encoder(object):
    def __init__(self, destination):
        self._destination = destination

    def write(self, b):
        raise NotImplementedError

    def close(self):
        self.flush()
        self._destination.flush()

    def flush(self):
        pass


class Decoder(object):
    def __init__(self, source):
        self._source = source

    def read(self, n=-1):
        raise NotImplementedError

    def close(self):
        pass


class PassThrough(Filter):
    def encoder(self, destination):
        return PassThroughEncoder(destination)

    def decoder(self, source):
        return PassThroughDecoder(source)


class PassThroughEncoder(Encoder):
    def write(self, b):
        return self._destination.write(b)


class PassThroughDecoder(Decoder):
    def read(self, n=-1):
        return self._source.read(n)


class ASCIIHexDecode(Filter):
    def encoder(self, destination):
        return ASCIIHexEncoder(destination)

    def decoder(self, source):
        return ASCIIHexDecoder(source)


class ASCIIHexEncoder(Encoder):
    def write(self, b):
        self._destination.write(hexlify(b))


class ASCIIHexDecoder(Decoder):
    def read(self, n=-1):
        # TODO: remove spaces
        # TODO: handle odd-lenght input to unhexlify
        # TODO: handler > EOD marker (also after odd-length string)
        return unhexlify(self._source.read(n))


class ASCII85Decode(Filter):
    def encoder(self, destination):
        return ASCII85Encoder(destination)

    def decoder(self, source):
        return ASCII85Decoder(source)

try:
    from base64 import a85encode, a85decode

    @consumer
    def ascii85_encoder(destination):
        rest = b''
        while True:
            try:
                in_bytes = rest + (yield)
            except GeneratorExit:
                break
            rest_len = len(in_bytes) % 4
            if rest_len:
                input, rest = in_bytes[:-rest_len], in_bytes[-rest_len:]
            else:
                input, rest = in_bytes, b''
            destination.write(a85encode(input))
        destination.write(a85encode(rest))
        destination.write(b'~>')  # EOD marker


    class ASCII85Encoder(Encoder):
        def __init__(self, destination):
            super().__init__(destination)
            self._encoder = ascii85_encoder(destination)

        def write(self, b):
            self._encoder.send(b)

        def flush(self):
            self._encoder.close()


    ASCII_WHITESPACE = whitespace.encode('ascii')

    class ASCII85Decoder(FIFOBuffer, Decoder):
        def __init__(self, source):
            super().__init__(source)
            self.rest = b''

        def read_from_source(self, n):
            out_data = b''
            while len(out_data) < n:
                in_data = self._source.read(n)
                in_data = self.rest + in_data.translate(None, ASCII_WHITESPACE)
                if not in_data:
                    self.rest = b''
                    break
                eod_index = in_data.find(b'~')
                if eod_index > 0:
                    assert in_data[eod_index:] == b'~>'
                    out_data += a85decode(in_data[:eod_index])
                    self.rest = b''
                    break
                rest_len = len(in_data) % 5
                if rest_len:
                    input, self.rest = in_data[:-rest_len], in_data[-rest_len:]
                else:
                    input, self.rest = in_data, b''
                out_data += a85decode(input)
            return out_data

except ImportError:
    class PythonVersionError(Exception):
        pass

    exc = PythonVersionError('The ASCII85Decode filter requires Python >= 3.4')

    class ASCII85Encoder(Encoder):
        def __init__(self, destination):
            raise exc


    class ASCII85Decoder(Decoder):
        def __init__(self, source):
            raise exc


from .cos import Name, Dictionary, Integer, Array, Null


class FlateDecodeParams(Dictionary):
    def __init__(self, predictor=None, colors=None, bits_per_component=None,
                 columns=None):
        super().__init__()
        if predictor:
            self['Predictor'] = Integer(predictor)
        if colors:
            self['Colors'] = Integer(colors)
        if bits_per_component:
            self['BitsPerComponent'] = Integer(bits_per_component)
        if columns:
            self['Columns'] = Integer(columns)

    @property
    def bytes_per_column(self):
        colors = self.get('Colors', 1)
        bits_per_component = self.get('BitsPerComponent', 8)
        columns = self.get('Columns', 1)
        return ceil(colors * bits_per_component / 8 * columns)


class FlateDecode(Filter):
    params_class = FlateDecodeParams

    def __init__(self, params=None, level=6):
        super().__init__(params)
        self.level = level

    def encoder(self, destination, bypass_predictor=False):
        if not bypass_predictor and self.params:
            raise NotImplementedError
        return FlateEncoder(destination, self.level)

    def decoder(self, source):
        decoded = FlateDecoder(source)
        if self.params and self.params['Predictor'] > 1:
            if self.params['Predictor'] >= 10:
                return PNGReconstructor(decoded, self.params.bytes_per_column)
            else:
                raise NotImplementedError
        else:
            return decoded


class FlateEncoder(Encoder):
    def __init__(self, destination, level):
        super().__init__(destination)
        self._compressor = zlib.compressobj(level)

    def write(self, b):
        self._destination.write(self._compressor.compress(b))

    def flush(self):
        self._destination.write(self._compressor.flush())


class FlateDecoder(FIFOBuffer, Decoder):
    def __init__(self, source):
        super().__init__(source)
        self._decompressor = zlib.decompressobj()

    def read_from_source(self, n):
        if self._decompressor is None:
            return b''
        in_data = self._source.read(n)
        out_data = self._decompressor.decompress(in_data)
        if len(in_data) == 0:
            out_data += self._decompressor.flush()
            self._decompressor = None
        elif len(out_data) == 0:
            out_data = self.read_from_source(n)
        return out_data


class LZWDecodeParams(FlateDecodeParams):
    def __init__(self, predictor=None, colors=None, bits_per_component=None,
                 columns=None, early_change=None):
        super().__init__(predictor, colors, bits_per_component, columns)
        if early_change:
            self['EarlyChange'] = Integer(early_change)


class LZWDecode(Filter):   # not implemented
    params_class = FlateDecodeParams


class PNGReconstructor(FIFOBuffer):
    NONE = 0
    SUB = 1
    UP = 2
    AVERAGE = 3
    PAETH = 4

    # TODO: bitsper...
    def __init__(self, source, bytes_per_column):
        super().__init__(source)
        self.bytes_per_column = bytes_per_column
        self._column_struct = struct.Struct('>{}B'.format(bytes_per_column))
        self._last_values = [0] * bytes_per_column

    def read_from_source(self, _n_ignored):
        # number of bytes requested `n` is ignored; a single row is fetched
        try:
            predictor, = struct.unpack('>B', self._source.read(1))
        except struct.error:
            return b''
        row = self._source.read(self._column_struct.size)
        values = list(self._column_struct.unpack(row))

        if predictor == self.NONE:
            out_row = row
        elif predictor == self.SUB:
            recon_a = 0
            for index, filt_x in enumerate(values):
                recon_a = values[index] = (filt_x + recon_a) % 256
            out_row = self._column_struct.pack(*values)
        elif predictor == self.UP:
            for index, (filt_x, recon_b) in enumerate(zip(values,
                                                          self._last_values)):
                values[index] = (filt_x + recon_b) % 256
            out_row = self._column_struct.pack(*values)
        elif predictor == self.AVERAGE:
            recon_a = 0
            for index, (filt_x, recon_b) in enumerate(zip(values,
                                                          self._last_values)):
                average = (recon_a + recon_b) // 2
                recon_a = values[index] = (filt_x + average) % 256
            out_row = self._column_struct.pack(*values)
        elif predictor == self.PAETH:
            recon_a = recon_c = 0
            for index, (filt_x, recon_b) in enumerate(zip(values,
                                                          self._last_values)):
                prediction = paeth_predictor(recon_a, recon_b, recon_c)
                recon_a = values[index] = (filt_x + prediction) % 256
            out_row = self._column_struct.pack(*values)

        self._last_values = values
        return out_row


def paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


class RunLengthDecode(Filter):
    def encoder(self, destination):
        return RunLengthEncoder(destination)

    def decoder(self, source):
        return RunLengthDecoder(source)


@consumer
def run_length_encoder(destination):
    def to_byte(value):
       return pack('B', value)

    def write_repeat(byte, count):
        destination.write(to_byte(257 - count))
        destination.write(byte)
        return b'', 1

    def flush(buffer):
        destination.write(to_byte(len(buffer) - 1))
        destination.write(buffer)
        return b''

    last_byte = yield
    buffer = b''
    same_count = 1
    while True:
        try:
            byte = yield
        except GeneratorExit:
            break
        if byte == b'':
            break
        if byte != last_byte:
            if same_count > 2:
                _, same_count = write_repeat(last_byte, same_count)
            else:
                if last_byte:
                    buffer += last_byte * same_count
                    same_count = 1
                if len(buffer) >= 127:  # not 128, as buffer can grow by 2
                    buffer = flush(buffer)
        else:
            same_count += 1
            if buffer and same_count > 2:
                buffer = flush(buffer)
            if same_count == 128:
                byte, same_count = write_repeat(last_byte, same_count)
        last_byte = byte
    if same_count > 2:
        _, same_count = write_repeat(last_byte, same_count)
    elif last_byte:
        buffer += last_byte * same_count
    if buffer:
        flush(buffer)
    destination.write(to_byte(128))


class RunLengthEncoder(Encoder):
    def __init__(self, destination):
        super().__init__(destination)
        self._encoder = run_length_encoder(destination)

    def write(self, b):
        for i in range(len(b)):
            self._encoder.send(b[i:i+1])

    def flush(self):
        self._encoder.close()


class RunLengthDecoder(FIFOBuffer, Decoder):
    def read_from_source(self, n):
        out_data = b''
        while len(out_data) < n:
            in_byte = self._source.read(1)
            if not in_byte:
                break
            length, = unpack('B', in_byte)
            if length == 128:
                break
            elif length < 128:
                out_data += self._source.read(length + 1)
            else:
                out_data += self._source.read(1) * (257 - length)
        return out_data


class CCITTFaxDecode(Filter):   # not implemented
    pass


class JBIG2Decode(Filter):   # not implemented
    pass


class DCTDecode(Filter):   # not implemented
    pass


class JPXDecode(Filter):   # not implemented
    pass


class Crypt(Filter):   # not implemented
    pass


class FilterPipeline(list):
    @property
    def name(self):
        return Array(Name(filter.name) for filter in self)

    @property
    def params(self):
        if not any(filter.params for filter in self):
            return None
        else:
            return Array(filter.params or Null() for filter in self)

    def encoder(self, destination):
        for filter in self:
            destination = filter.encoder(destination)
        return destination

    def decoder(self, source):
        for filter in self:
            source = filter.decoder(source)
        return source
