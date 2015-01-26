# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct, zlib

from binascii import hexlify, unhexlify
from math import ceil
from struct import pack, unpack

from ...util import consumer
from .util import FIFOBuffer


class Filter(object):
    params_class = None

    def __init__(self, params=None):
        if self.params_class is None:
            assert params is None
        self.params = params

    @property
    def name(self):
        return self.__class__.__name__

    def encoder(self, destination):
        raise NotImplementedError

    def decoder(self, source):
        raise NotImplementedError


class Encoder(object):
    def __init__(self, destination):
        self._destination = destination

    def write(self, b):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class Decoder(object):
    def __init__(self, source):
        self._source = source

    def read(self, n=-1):
        raise NotImplementedError


class PassThrough(Filter):
    def encoder(self, destination):
        return PassThroughEncoder(destination)

    def decoder(self, source):
        return PassThroughDecoder(source)


class PassThroughEncoder(Encoder):
    def write(self, b):
        return self._destination.write(b)

    def close(self):
        pass


class PassThroughDecoder(Decoder):
    def read(self, n=-1):
        return self._source.read(n)


class ASCIIHexDecode(Filter):
    def encoder(self, destination):
        return ASCIIHexEncoder(destination)

    def decode(self, source):
        return ASCIIHexDecoder(source)


class ASCIIHexEncoder(Encoder):
    def write(self, b):
        self._destination.write(hexlify(b))

    def close(self):
        pass


class ASCIIHexDecoder(Decoder):
    def read(self, n=-1):
        return unhexlify(self._source.read(n))


class ASCII85Decode(Filter):   # not implemented
    pass


from .cos import Dictionary, Integer


class FlateDecodeParams(Dictionary):
    def __init__(self, predictor=None, colors=None, bits_per_component=None,
                 columns=None):
        if predictor:
            self['Predictor'] = Integer(predictor)
        if colors:
            self['Colors'] = Integer(colors)
        if colors:
            self['BitsPerComponent'] = Integer(bits_per_component)
        if colors:
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

    def encoder(self, destination):
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

    def close(self):
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
            out_data = self.read_from_source(self, n)
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
        predictor = struct.unpack('>B', self._source.read(1))[0]
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

    def close(self):
        self._encoder.close()


class RunLengthDecoder(FIFOBuffer, Decoder):
    def read_from_source(self, n):
        out_data = b''
        while True:
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
            if len(out_data) >= n:
                break
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
