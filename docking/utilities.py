def grouper(n, iterable):
    iterable = list(iterable)
    out = []
    for i in range(0, len(iterable), n):
        out += [iterable[i: i+n]]
    return out