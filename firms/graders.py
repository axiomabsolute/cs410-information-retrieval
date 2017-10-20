from collections import Counter
from itertools import groupby
from operator import itemgetter
from firms.models import flatten

# A grader is a function: Function[Dictionary[index_type, snippets], Dictionary[piece_name, Dictionary[offset, grade]]

def simple_sum_grader(snippets_by_index_type):
    by_piece = itemgetter('piece')
    by_offset = itemgetter('offset')
    snippets = flatten(snippets_by_index_type.values())
    snippets.sort(key=by_piece)
    grades_by_piece_and_offset = {k:Counter(map(by_offset, g)) for k,g in groupby(snippets, by_piece)}
    return grades_by_piece_and_offset
