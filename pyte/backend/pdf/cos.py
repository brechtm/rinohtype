
from collections import OrderedDict
from io import StringIO


PDF_VERSION = '1.4'


# TODO: encoding
# TODO: max line length (not streams)


class Object(object):
    def __init__(self, document=None):
        self.document = document
        if document:
            document.append(self)
        else:
            self.identifier = None
        self.generation = 0

    @property
    def is_direct(self):
        return self.identifier is None

    def __str__(self):
        if self.is_direct:
            out = self.string()
        else:
            out = '{} {} obj\n'.format(self.identifier, self.generation)
            out += '  {}\n'.format(self.string())
            out += 'endobj'
        return out

    def string(self):
        raise NotImplementedError

    @property
    def reference(self):
        return '{} {} R'.format(self.identifier, self.generation)



class Boolean(Object):
    def __init__(self, value, document=None):
        super().__init__(document)
        self.value = value

    def string(self):
        return 'true' if self.value else 'false'


class Integer(Object, int):
    def __init__(self, value, document=None):
        Object.__init__(self, document)

    def string(self):
        return int.__str__(self)


class Real(Object, float):
    def __init__(self, value, document=None):
        Object.__init__(self, document)

    def string(self):
        return float.__str__(self)


class String(Object):
    def __init__(self, string, document=None):
        super().__init__(document)
        self.value = value

    def string(self):
        return self.string


class Name(Object):
    # TODO: names should be unique, check
    def __init__(self, name, document=None):
        super().__init__(document)
        self.name = name

    def string(self):
        return '/{}'.format(self.name)


class Array(Object, list):
    def __init__(self, items=[], document=None):
        Object.__init__(self, document)
        list.__init__(self, items)

    def string(self):
        return '[{}]'.format(' '.join(map(str, self)))


class Dictionary(Object, OrderedDict):
    def __init__(self, document=None):
        Object.__init__(self, document)
        OrderedDict.__init__(self)

    def string(self):
        return '<< ' + ' '.join([str(Name(key)) + ' ' + str(value)
                                 for key, value in self.items()]) + ' >>'


class Stream(Object, StringIO):
    def __init__(self, document):
        Object.__init__(self, document)
        StringIO.__init__(self)

    def string(self):
        dictionary = Dictionary()
        dictionary['Length'] = Integer(self.tell())
        out = str(dictionary)
        out += '\nstream\n'
        out += self.getvalue()
        out += '\nendstream'
        return out


class Null(Object):
    def __init__(self):
        pass



class Document(object):
    def __init__(self):
        self._identifier = 0
        self.objects = []
        self.xref_table = XRefTable()
        self.pages = Pages(self)
        self.catalog = Catalog(self)
        self.catalog['Pages'] = self.pages.reference

    def append(self, obj):
        obj.identifier = self.next_identifier
        self.objects.append(obj)

    @property
    def next_identifier(self):
        self._identifier += 1
        return self._identifier

    def write(self, file):
        def out(string):
            file.write(string.encode('ascii') + b'\n')

        out('%PDF-' + PDF_VERSION)
        file.write(b'%\xDC\xE1\xD8\xB7\n')
        for obj in self.objects:
            self.xref_table.append(obj, file.tell())
            out(str(obj))
        xref_table_address = file.tell()
        out(str(self.xref_table))
        out('trailer')
        trailer_dict = Dictionary()
        trailer_dict['Size'] = Integer(len(self.xref_table))
        trailer_dict['Root'] = self.catalog.reference
        #trailer_dict['Info'] = # TODO: ref to info dict
        #trailer_dict['ID'] = # TODO: hash of all data
        out(str(trailer_dict))
        out('startxref')
        out('{}'.format(xref_table_address))
        out('%%EOF')


class XRefTable(object):
    def __init__(self):
        self.objects = []
        self.addresses = []

    def append(self, obj, address):
        self.objects.append(obj)
        self.addresses.append(address)

    def __len__(self):
        return len(self.objects) + 1

    def __str__(self):
        out = 'xref'
        out += '\n0 {}'.format(len(self.objects) + 1)
        out += '\n0000000000 65535 f '
        for obj, address in zip(self.objects, self.addresses):
            out += '\n{:010d} {:05d} n '.format(address, obj.generation)
        return out


class Catalog(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Catalog')


class Pages(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Pages')
        self['Count'] = Integer(0)
        self['Kids'] = Array()

    def new_page(self, width, height):
        page = Page(self, width, height)
        self['Kids'].append(page.reference)
        self['Count'] = Integer(self['Count'] + 1)
        return page


class Page(Dictionary):
    def __init__(self, parent, width, height):
        super().__init__(parent.document)
        self['Type'] = Name('Page')
        self['Parent'] = parent.reference
        self['Resources'] = Dictionary()
        self['MediaBox'] = Array([0, 0, float(width), float(height)])


class Font(Dictionary):
    def __init__(self, document):
        super().__init__(document)
        self['Type'] = Name('Font')


##class Canvas(StringIO):
##    def __init__(self):
##        super().__init__(self)


