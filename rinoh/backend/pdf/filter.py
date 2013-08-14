# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct, zlib

from binascii import hexlify, unhexlify
from math import floor, ceil

from .util import FIFOBuffer


class Filter(object):
    params_class = None

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
    def read(self, b):
        return self._destination.read(n)


class ASCIIHexDecode(Filter):
    def encoder(self, destination):
        return ASCIIHexEncoder(destination)

    def decode(self, source):
        return ASCIIHexDecoder(source)


class ASCIIHexEncoder(Decoder):
    def write(self, b):
        self._destination.write(hexlify(b))

    def close(self):
        pass


class ASCIIHexDecoder(Decoder):
    def read(self, n=-1):
        return unhexlify(self._source.read(n))


class ASCII85Decode(Filter):
    def encode(self, data):
        raise NotImplementedError

    def decode(self, data):
        raise NotImplementedError


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
        super().__init__()
        self.params = params
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
            self['EarlyChange'] = cos.Integer(early_change)


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

    def read_from_source(self, n):
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
