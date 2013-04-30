# cython: profile=True
cimport cython
from psg.exceptions import PFBError

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr)
    void *malloc(size_t size)
    void *realloc(void *ptr, size_t size)
    size_t strlen(char *s)
    char *strcpy(char *dest, char *src)


def pfb2pfa(pfb, pfa):
    """
    Convert a PostScript Type1 font in binary representation (pfb) to
    ASCII representation (pfa). This function is modeled after the
    pfb2pfa program written in C by Piet Tutelaers. I freely admit
    that I understand only rudimentarily what I'm doing here.
    """

    cdef int r, t, c, l, l1, l2, l3, l4, ptr
    cdef int length, i
    cdef int* pfb_content

    pfb_content_py = pfb.read()
    length = len(pfb_content_py)
    pfb_content = <int*>malloc(length * sizeof(int))
    for i in range(length):
        pfb_content[i] = pfb_content_py[i]
    ptr = 0

    while True:
        r = pfb_content[ptr]; ptr += 1
        if r != 128:
            raise PFBError("Not a pfb file!")

        t = pfb_content[ptr]; ptr += 1

        if t == 1 or t == 2:
            l1 = pfb_content[ptr]; ptr += 1
            l2 = pfb_content[ptr]; ptr += 1
            l3 = pfb_content[ptr]; ptr += 1
            l4 = pfb_content[ptr]; ptr += 1

            l = l1 | l2 << 8 | l3 << 16 | l4 << 24

        if t == 1:
            for i in range(l):
                c = pfb_content[ptr]; ptr += 1
                if c == "\r":
                    pfa.write("\n")
                else:
                    pfa.write(bytes((c, )).decode('ASCII'))
        elif t == 2:
            for i in range(l):
                c = pfb_content[ptr]; ptr += 1
                pfa.write("%02x" % c)
                if (i + 1) % 30 == 0:
                    pfa.write("\n")

            pfa.write("\n")
        elif t == 3:
            free(pfb_content)
            break
        else:
            raise PFBError("Error in PFB file: unknown field type %i!" % t)

