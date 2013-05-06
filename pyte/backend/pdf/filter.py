
import zlib

from binascii import hexlify



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
        self._compressor = zlib.compressobj(level)
        self._decompressor = zlib.decompressobj()
        self._mode = None

    def encode(self, data):
        if self._mode:
            assert self._mode == 'compress'
        else:
            self._mode = 'compress'
        return self._compressor.compress(data)

    def decode(self, data):
        if self._mode:
            assert self._mode == 'decompress'
        else:
            self._mode = 'decompress'
        return self._decompressor.decompress(data)

    def finish(self):
        if self._mode == 'compress':
            return self._compressor.flush()
        elif self._mode == 'decompress':
            return self._decompressor.flush()
        else:
            return b''
