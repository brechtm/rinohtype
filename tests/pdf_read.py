
from rinoh.backend.pdf.reader import PDFReader



if __name__ == '__main__':
    pdf = PDFReader('../examples/rfic2009/template.pdf')
    print(pdf.catalog)
    print(pdf.info)
    print(pdf.id)
    print(pdf.catalog['Pages']['Kids'])
    print(pdf.catalog['Pages']['Kids'][0])
    print(pdf.catalog['Pages']['Kids'][0]['Contents'])
    pdf.write('template_out.pdf')
