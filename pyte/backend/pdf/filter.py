
import zlib

from binascii import hexlify, unhexlify

from .util import FIFOBuffer


class Filter(object):
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


class FlateDecode(Filter):
    def __init__(self, level=6):
        super().__init__()
        self.level = level

    def encoder(self, source):
        return FlateEncoder(source, self.level)

    def decoder(self, source):
        return FlateDecoder(source)


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
