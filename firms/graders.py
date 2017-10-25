from collections import Counter, defaultdict
from itertools import groupby
from operator import attrgetter, itemgetter
from math import log
from firms.models import flatten, GraderResult

# A grader receives a list of GraderMatch tuples
# and ultimately produces GraderResult tuples

def by(*getters):
    def _by(item):
        result = item
        for getter in getters:
            result = getter(result)
        return result
    return _by

by_snippet = attrgetter('snippet')
by_piece = itemgetter('piece')
by_offset = itemgetter('offset')
by_part = itemgetter('part')
by_stemmer = attrgetter('stemmer')
by_snippet_piece = by(by_snippet, by_piece)
by_snippet_part = by(by_snippet, by_part)
by_snippet_offset = by(by_snippet, by_offset)

def count_grader(matches):
    matches.sort(key=by_snippet_piece)
    grades_by_piece = {k:len(list(g)) for k,g in groupby(matches, by_snippet_piece)}
    return ( GraderResult(piece=k, grade=v, meta={}) for k,v in grades_by_piece.items())

def log_count_grader(matches):
    result = defaultdict(lambda: 0)
    matches.sort(key=by_snippet_piece)
    for piece,piece_matches in groupby(matches, by_snippet_piece):
        for _,stemmer_matches in groupby(piece_matches, by_stemmer):
            result[piece] = result[piece] + log(len(list(stemmer_matches)))
    return ( GraderResult(piece=k, grade=v, meta={}) for k,v in result.items())