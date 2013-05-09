
import zlib

from binascii import hexlify

from .util import FIFOBuffer


class Filter(object):
    def __init__(self):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    def encode(self, data):
        raise NotImplementedError

    def decode(self, data):
        raise NotImplementedError


class ASCIIHexDecode(Filter):
    def encode(self, data):
        return hexlify(data)

    def decode(self, data):
        return unhexlify(data)


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
        return FlateEncoder(source, level)

    def decoder(self, source):
        return FlateDecoder(source)


class FlateDecoder(FIFOBuffer):
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
