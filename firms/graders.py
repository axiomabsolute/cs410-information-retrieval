from collections import Counter, defaultdict
from itertools import groupby
from operator import attrgetter, itemgetter
from math import log
from firms.models import flatten, GraderResult

def by(*getters):
    def _by(item):
        result = item
        for getter in getters:
            result = getter(result)
        return result
    return _by

# Named tuples use attrgetter
by_snippet = attrgetter('snippet')
by_stemmer = attrgetter('stemmer')

# Dictionaries use itemgetter
by_piece = itemgetter('piece')
by_offset = itemgetter('offset')
by_part = itemgetter('part')
by_snippet_piece = by(by_snippet, by_piece)
by_snippet_part = by(by_snippet, by_part)
by_snippet_offset = by(by_snippet, by_offset)

# Not a grader - one step above before aggrating by piece
def stem_counter_by_piece(matches):
    result = {}
    matches.sort(key=by_snippet_piece)
    for piece,piece_matches in groupby(matches, by_snippet_piece):
        result[piece] = Counter(map(by_stemmer, piece_matches))
    return result

# For optimizing the log weighted sum grader
def log_weighted_sum_grader_weightless_factory(stemmer_matches, tp_names, weight_keys):
    """
    Given a set of matches and the name of the true-positive result, returns a function which expects an array of weights
    and returns the ranking of the true-positive result.

    stemmer_matches list of lists of stemmer matches for each query
    tp_names name of true positive results, corresponding to stemmer_matches

    returns average rank of true-positive results
    """
    ignore = set()
    def _inner(weights):
        ranks = []
        grader = log_weighted_count_sum_grader_factory(dict(zip(weight_keys, weights)))
        for (matches, tp_name) in zip(stemmer_matches, tp_names):
            # Run grader on matches
            grades = grader(matches)
            # Find rank of true-positive
            sorted_by_grade = list(sorted(grades, key=attrgetter('grade'), reverse=True))
            tp_result = [i for i,x in enumerate(sorted_by_grade) if x.piece == tp_name]
            # Add rank to ranks
            try:
                if not tp_name in ignore:
                    ranks.append(tp_result[0])
            except IndexError:
                print("\t\t\tIgnoring %s" % tp_name)
                ignore.add(tp_name)

        # Find average rank
        avg_rank = sum(ranks)/len(ranks)
        return avg_rank
    return _inner

def count_aggregate_grader_by_stemmer(aggregator):
    # matches is a dictionary from piece name to dictionary of stemmer to counts
    def aggregate_grader(matches):
        result = defaultdict(lambda: 0)
        for piece,stemmer_entries in matches.items():
            for stemmer,stemmer_count in stemmer_entries.items():
                result[piece] = result[piece] + aggregator(stemmer, stemmer_count)
        return ( GraderResult(piece=k, grade=v, meta={}) for k,v in result.items())
    return aggregate_grader

def log_weighted_count_sum_grader_factory(weights_by_stemmer):
    return count_aggregate_grader_by_stemmer(lambda stemmer,stemmer_count: weights_by_stemmer[stemmer] * log(stemmer_count))

# A grader receives a list of GraderMatch tuples
# and ultimately produces GraderResult tuples
def count_grader(matches):
    matches.sort(key=by_snippet_piece)
    grades_by_piece = {k:len(list(g)) for k,g in groupby(matches, by_snippet_piece)}
    return ( GraderResult(piece=k, grade=v, meta={}) for k,v in grades_by_piece.items())

def aggregate_grader_by_stemmer(aggregator):
    def aggregate_grader(matches):
        result = defaultdict(lambda: 0)
        matches.sort(key=by_snippet_piece)
        for piece,piece_matches in groupby(matches, by_snippet_piece):
            for stemmer,stemmer_matches in groupby(piece_matches, by_stemmer):
                result[piece] = result[piece] + aggregator(stemmer, stemmer_matches)
        return ( GraderResult(piece=k, grade=v, meta={}) for k,v in result.items())
    return aggregate_grader

log_count_grader = aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: log(len(list(stemmer_matches))))

def weighted_sum_grader_factory(weights_by_stemmer):
    return aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: weights_by_stemmer[stemmer] * len(list(stemmer_matches)))

def log_weighted_sum_grader_factory(weights_by_stemmer):
    return aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: weights_by_stemmer[stemmer] * log(len(list(stemmer_matches))))
