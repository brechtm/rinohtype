
import hashlib, math, struct
from datetime import datetime, timedelta


def grab(file, data_format):
    data = file.read(struct.calcsize(data_format))
    return struct.unpack('>' + data_format, data)


def grab_datetime(file):
    return datetime(1904, 1, 1, 12) + timedelta(seconds=grab(file, 'Q')[0])


# using the names and datatypes from the OpenType specification
# http://www.microsoft.com/typography/otspec/

byte = lambda file: grab(file, 'B')[0]
char = lambda file: grab(file, 'b')[0]
ushort = lambda file: grab(file, 'H')[0]
short = lambda file: grab(file, 'h')[0]
ulong = lambda file: grab(file, 'L')[0]
long = lambda file: grab(file, 'l')[0]
fixed = lambda file: grab(file, 'L')[0] / 2**16
fword = short
ufword = ushort
longdatetime = lambda file: grab_datetime(file)
string = lambda file: grab(file, '4s')[0].decode('ascii')


def array(reader, length):
    return lambda file: [reader(file) for i in range(length)]


def calculate_checksum(file, offset, length, head=False):
    tmp = 0
    file.seek(offset)
    end_of_data = offset + 4 * math.ceil(length / 4)
    while file.tell() < end_of_data:
        uint32 = grab(file, 'L')[0]
        if not (head and file.tell() == offset + 12):
            tmp += uint32
    return tmp % 2**32


PLATFORM_UNICODE = 0
PLATFORM_MACINTOSH = 1
PLATFORM_ISO = 2
PLATFORM_WINDOWS = 3
PLATFORM_CUSTOM = 4

NAME_COPYRIGHT = 0
NAME_FAMILTY = 1
NAME_SUBFAMILY = 2
NAME_UID = 3
NAME_FULL = 4
NAME_VERSION = 5
NAME_PS_NAME = 6
NAME_TRADEMARK = 7
NAME_MANUFACTURER = 8
NAME_DESIGNER = 9
NAME_DESCRIPTION = 10
NAME_VENDOR_URL = 11
NAME_DESIGNER_URL = 12
NAME_LICENSE = 13
NAME_LICENSE_URL = 14
NAME_PREFERRED_FAMILY = 16
NAME_PREFERRED_SUBFAMILY = 17
# ...


def decode(platform_id, encoding_id, data):
    try:
        return data.decode(encodings[platform_id][encoding_id])
    except KeyError:
        raise NotImplementedError()


encodings = {}

encodings[PLATFORM_UNICODE] = {}

UNICODE_1_0 = 0
UNICODE_1_1 = 1
UNICODE_ISO_IEC_10646 = 2
UNICODE_2_0_BMP = 3
UNICODE_2_0_FULL = 4
UNICODE_VAR_SEQ = 5
UNICODE_FULL = 6

encodings[PLATFORM_MACINTOSH] = {}

encodings[PLATFORM_ISO] = {}

ISO_ASCII = 0
ISO_10646 = 1
ISO_8859_1 = 2

encodings[PLATFORM_WINDOWS] = {1: 'utf_16_be',
                               2: 'cp932',
                               3: 'gbk',
                               4: 'cp950',
                               5: 'euc_kr',
                               6: 'johab',
                               10: 'utf_32_be'}

