from collections import Counter
from firms.models import flatten

# A grader is a function: Function[Dictionary[index_type, snippets], Dictionary[piece_name, number]

# Each time the query matches a snippet from a piece for each index, give it a score of 1, and sum them
def simple_sum_grader(snippets_by_index_type):
    snippets = flatten(snippets_by_index_type.values())
    return Counter([snippet.piece for snippet in snippets])