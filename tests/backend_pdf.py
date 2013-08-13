
from io import StringIO, BytesIO

from rinoh.backend.pdf.cos import (Document, Boolean, Catalog, String,
                                  Dictionary, Stream, XObjectForm)
from rinoh.backend.pdf.reader import PDFReader



image = PDFReader('../examples/rfic2009/fig2.pdf')
image_page = image.catalog['Pages']['Kids'][0]

d = Document()

b = Boolean(True, indirect=True)

page = d.catalog['Pages'].new_page(100, 150)

page['Resources']['XObject'] = Dictionary()
page['Resources']['XObject']['Im01'] = image_page.to_xobject_form()

page['Contents'] = Stream()
page['Contents'].write(b'0.2 0 0 0.2 30 30 cm')
page['Contents'].write('/Im01 Do'.encode('utf_8'))

file = open('backend_pdf.pdf', 'wb')
d.write(file)

file.close()
