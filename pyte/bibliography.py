
# http://sourceforge.net/mailarchive/message.php?msg_id=25355232

# http://dret.net/bibconvert/tex2unicode

#from citeproc import

import re
from lxml import objectify
from warnings import warn

from .util import set_xml_catalog
from .warnings import PyteWarning


class CustomDict(dict):
    def __init__(self, required, optional):
        self.update(optional)
        self.update(required)

    def __getattr__(self, name):
        return self[name]


class Reference(CustomDict):
    def __init__(self, id, type, title, authors, **optional):
        required = {'id': id, 'type': type, 'title': title, 'author': authors}
        super().__init__(required, optional)


class Name(CustomDict):
    def __init__(self, given, family, **optional):
        required = {'given': given, 'family': family}
        super().__init__(required, optional)

    def given_initials(self):
        names = re.split(r'[- ]', self.given)
        return ' '.join('{}.'.format(name[0]) for name in names)


class Date(CustomDict):
    def __init__(self, year, **optional):
        required = {'year': year}
        super().__init__(required, optional)



class Bibliography(list):
    def __init__(self, source, formatter):
        self.source = source
        self.formatter = formatter
        formatter.bibliography = self

    def cite(self, id):
        try:
            reference = self.source[id]
        except KeyError:
            warning = "Unknown reference ID '{}'".format(id)
            warn(warning, PyteWarning)
            return "[{}]".format(warning)
        self.append(reference)
        return self.formatter.format_citation(reference)

    def bibliography(self, target):
        return self.formatter.format_bibliography(target)


class BibliographyFormatter(object):
    def __init__(self):
        pass

    def format_citation(self, reference):
        raise NotImplementedError

    def format_bibliography(self, target):
        raise NotImplementedError


class BibliographySource(dict):
    def add(self, entry):
        self[entry.id] = entry


class PseudoCSLDataXML(BibliographySource):
    def __init__(self, filename):
        set_xml_catalog()
        self.parser = objectify.makeparser(remove_comments=True,
                                           no_network=True)
        self.xml = objectify.parse(filename, self.parser)
        self.root = self.xml.getroot()
        for ref in self.root.ref:
            self.add(self.parse_reference(ref))

    def parse_reference(self, ref):
        authors = []
        for name in ref.author.name:
            authors.append(self.parse_name(name))
        id = str(ref.attrib['id'])
        issued = self.parse_date(ref.issued)
        return Reference(id, ref.type.text, ref.title.text, authors,
                         container_title=ref.find('container-title').text, issued=issued)

    def parse_name(self, name):
        return Name(name.given.text, name.family.text)

    def parse_date(self, date):
        return Date(date.year.text, month=date.month.text)


class BibTeX(BibliographySource):
    pass


class MODS(BibliographySource):
    pass