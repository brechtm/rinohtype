# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from io import BytesIO, SEEK_END


class FIFOBuffer(object):
    def __init__(self, source, buffer_size=4096):
        self._source = source
        self._buffer_size = buffer_size
        self._fifo = BytesIO()
        self._write_pos = 0
        self._read_pos = 0

    @property
    def size(self):
        return self._write_pos - self._read_pos

    def read_from_source(self, n):
        raise NotImplementedError

    def fill_buffer(self):
        self._fifo.seek(self._write_pos)
        data = self.read_from_source(self._buffer_size)
        self._fifo.write(data)
        self._write_pos = self._fifo.tell()
        return len(data) > 0

    def read(self, n=-1):
        while n is None or n < 0 or self.size < n:
            if not self.fill_buffer():
                break
        self._fifo.seek(self._read_pos)
        out = self._fifo.read(n)
        self._read_pos = self._fifo.tell()
        if self._read_pos >= self._buffer_size:
            self._fifo = BytesIO(self._fifo.read())
            self._write_pos = self._fifo.seek(0, SEEK_END)
            self._read_pos = 0
        return out

    def close(self):
        pass
