
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
        self.level = level

    def encode(self, data):
        return zlib.compress(data, self.level)

    def decode(self, data):
        return zlib.decompress(data)
