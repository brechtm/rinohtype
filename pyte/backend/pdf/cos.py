
from collections import OrderedDict
from io import BytesIO, SEEK_END



PDF_VERSION = '1.4'


# TODO: max line length (not streams)


class Object(object):
    def __init__(self, document=None):
        if document is not None:
            self.document = document
            self.reference = document.append(self)

    def bytes(self):
        try:
            out = self.reference.bytes()
        except AttributeError:
            out = self._bytes()
        return out


# TODO: forward method calls to referred object (metaclass?)
class Reference(object):
    def __init__(self, document, identifier, generation):
        self.document = document
        self.identifier = identifier
        self.generation = generation

    def bytes(self):
        return '{} {} R'.format(self.identifier,
                                self.generation).encode('utf_8')

    @property
    def target(self):
        return self.document[self.identifier][0]

    def __repr__(self):
        return '{}<{} {}>'.format(self.target.__class__.__name__,
                                  self.identifier, self.generation)

    def __getitem__(self, name):
        return self.target[name]

    def __getattr__(self, name):
        return getattr(self.target, name)


class Boolean(Object):
    def __init__(self, value, document=None):
        super().__init__(document)
        self.value = value

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.value)

    def _bytes(self):
        return b'true' if self.value else b'false'


class Integer(Object, int):
    def __new__(cls, value, base=10, document=None, hex=False):
        try:
            return int.__new__(cls, value, base)
        except TypeError:
            return int.__new__(cls, value)


    def __init__(self, value, base=10, document=None, hex=False):
        Object.__init__(self, document)
        self.hex = hex

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, int.__repr__(self))

    def _bytes(self):
        if self.hex:
            out = '<{:x}>'.format(self).encode('utf_8')
        else:
            out = int.__str__(self).encode('utf_8')
        return out


class Real(Object, float):
    def __init__(self, value, document=None):
        Object.__init__(self, document)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, float.__repr__(self))

    def _bytes(self):
        return float.__str__(self).encode('utf_8')


class String(Object):
    def __init__(self, string, document=None):
        super().__init__(document)
        self.value = string

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.value)

    def _bytes(self):
        escaped = self.value.replace('\n', r'\n')
        escaped = escaped.replace('\r', r'\r')
        escaped = escaped.replace('\t', r'\t')
        escaped = escaped.replace('\b', r'\b')
        escaped = escaped.replace('\f', r'\f')
        for char in '\\()':
            escaped = escaped.replace(char, '\\{}'.format(char))
        return '({})'.format(escaped).encode('utf_8')


class Name(Object):
    def __init__(self, name, document=None):
        super().__init__(document)
        self.name = name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def _bytes(self):
        # TODO: # escaping
        return '/{}'.format(self.name).encode('utf_8')


class Array(Object, list):
    def __init__(self, items=[], document=None):
        Object.__init__(self, document)
        list.__init__(self, items)

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__, list.__repr__(self))

    def _bytes(self):
        return b'[' + (b' '.join([elem.bytes() for elem in self])) + b']'


class Dictionary(Object, OrderedDict):
    def __init__(self, document=None):
        Object.__init__(self, document)
        OrderedDict.__init__(self)

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__, dict.__repr__(self))

    def _bytes(self):
        return b'<< ' + b' '.join([Name(key).bytes() + b' ' + value.bytes()
                                   for key, value in self.items()]) + b' >>'


class Stream(Object, BytesIO):
    def __init__(self, document):
        # the document argument is required
        # (Streams are always indirectly referenced)
        Object.__init__(self, document)
        BytesIO.__init__(self)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.size)

    def _bytes(self):
        dictionary = Dictionary()
        dictionary['Length'] = Integer(self.size)
        out = dictionary.bytes()
        out += b'\nstream\n'
        out += self.getvalue()
        out += b'\nendstream'
        return out

    @property
    def size(self):
        restore_pos = self.tell()
        self.seek(0, SEEK_END)
        size = self.tell()
        self.seek(restore_pos)
        return size


class Null(Object):
    def __init__(self, document=None):
        super().__init__(document)

    def __repr__(self):
        return self.__class__.__name__

    def _bytes(self):
        return b'null'



class Document(dict):
    def __init__(self):
        self.catalog = Catalog(self)
        self.info = None
        self.id = None

    def append(self, obj):
        identifier, generation = self.max_identifier + 1, 0
        self[identifier] = (obj, generation)
        return Reference(self, identifier, generation)

    @property
    def max_identifier(self):
        try:
            identifier = max(self.keys())
        except ValueError:
            identifier = 0
        return identifier

    def _write_xref_table(self, file, addresses):
        def out(string):
            file.write(string + b'\n')

        out(b'xref')
        out('0 {}'.format(self.max_identifier + 1).encode('utf_8'))
        out(b'0000000000 65535 f ')
        last_free = 0
        for identifier in range(1, self.max_identifier + 1):
            try:
                obj, generation = self[identifier]
                address = addresses[identifier]
            except KeyError:
                address = last_free = identifier
                generation = 0
            out('{:010d} {:05d} n '.format(address, generation).encode('utf_8'))

    def write(self, file_or_filename):
        def out(string):
            file.write(string + b'\n')

        try:
            file = open(file_or_filename, 'wb')
        except TypeError:
            file = file_or_filename
        out('%PDF-{}'.format(PDF_VERSION).encode('utf_8'))
        file.write(b'%\xDC\xE1\xD8\xB7\n')
        addresses = {}
        for identifier in range(1, self.max_identifier + 1):
            obj, generation = self[identifier]
            try:
                obj, generation = self[identifier]
                addresses[identifier] = file.tell()
                out('{} 0 obj'.format(identifier, generation).encode('utf_8'))
                out(obj._bytes())
                out(b'endobj')
            except KeyError:
                pass
        xref_table_address = file.tell()
        self._write_xref_table(file, addresses)
        out(b'trailer')
        trailer_dict = Dictionary()
        trailer_dict['Size'] = Integer(self.max_identifier + 1)
        trailer_dict['Root'] = self.catalog.reference
        if self.info:
            trailer_dict['Info'] = self.info.reference
        if self.id:
            # TODO: hash of all data
            trailer_dict['ID'] = self.id
        out(trailer_dict.bytes())
        out(b'startxref')
        out(str(xref_table_address).encode('utf_8'))
        out(b'%%EOF')


class Catalog(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Catalog')
        self['Pages'] = Pages(self.document)


class Pages(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Pages')
        self['Count'] = Integer(0)
        self['Kids'] = Array()

    def new_page(self, width, height):
        page = Page(self, width, height)
        self['Kids'].append(page)
        self['Count'] = Integer(self['Count'] + 1)
        return page


class Page(Dictionary):
    def __init__(self, parent, width, height):
        super().__init__(parent.document)
        self['Type'] = Name('Page')
        self['Parent'] = parent
        self['Resources'] = Dictionary()
        self['MediaBox'] = Array([Integer(0), Integer(0),
                                  Real(width), Real(height)])


class Font(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Font')
