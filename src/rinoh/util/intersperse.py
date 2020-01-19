def intersperse(iterable, element):
    """Generator yielding all elements of `iterable`, but with `element`
    inserted between each two consecutive elements"""
    iterable = iter(iterable)
    yield next(iterable)
    while True:
        try:
            next_from_iterable = next(iterable)
            yield element
            yield next_from_iterable
        except StopIteration:
            return
