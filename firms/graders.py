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
by_lookup_match = attrgetter('lookup_match')
by_stemmer = attrgetter('stemmer')

# Dictionaries use itemgetter
by_offset = itemgetter('offset')
by_part = itemgetter('part')
by_path = itemgetter('path')
by_piece = itemgetter('piece')
by_stem = itemgetter('stem')
by_lookup_match_offset = by(by_lookup_match, by_offset)
by_lookup_match_part = by(by_lookup_match, by_part)
by_lookup_match_path = by(by_lookup_match, by_path)
by_lookup_match_piece = by(by_lookup_match, by_piece)
by_lookup_match_stem = by(by_lookup_match, by_stem)

# Not a grader - one step above before aggrating by piece
def stem_counter_by_piece(matches):
    result = {}
    matches.sort(key=by_lookup_match_piece)
    for piece,piece_matches in groupby(matches, by_lookup_match_piece):
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
def count_grader(matches, num_pieces):
    matches.sort(key=by_lookup_match_piece)
    grades_by_piece = {k:len(list(g)) for k,g in groupby(matches, by_lookup_match_piece)}
    return ( GraderResult(piece=k, grade=v, meta={}) for k,v in grades_by_piece.items())

def aggregate_grader_by_stemmer(aggregator):
    def aggregate_grader(matches, corpus_size):
        result = defaultdict(lambda: 0)
        matches.sort(key=by_lookup_match_piece)
        for piece,piece_matches in groupby(matches, by_lookup_match_piece):
            for stemmer,stemmer_matches in groupby(piece_matches, by_stemmer):
                result[piece] = result[piece] + aggregator(stemmer, stemmer_matches)
        return ( GraderResult(piece=k, grade=v, meta={}) for k,v in result.items())
    return aggregate_grader

log_count_grader = aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: log(len(list(stemmer_matches))))

def weighted_sum_grader_factory(weights_by_stemmer):
    return aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: weights_by_stemmer[stemmer] * len(list(stemmer_matches)))

def log_weighted_sum_grader_factory(weights_by_stemmer):
    return aggregate_grader_by_stemmer(lambda stemmer,stemmer_matches: weights_by_stemmer[stemmer] * log(len(list(stemmer_matches))))

def bm25_idf(N, df):
    return log( (N - df + 0.5) / (df + 0.5) )

def bm25_tf(tf, k=1.2):
    return (tf * (k + 1) )/(tf + k)

def bm25_factory():
    def bm25(matches, number_of_pieces):
        # Given a list of (stemmer, snippet) pairs
        # Compute DF - Dictionary from stem -> piece count
        dfs = {}
        for stem, stem_matches in groupby(sorted(matches, key=by_lookup_match_stem), by_lookup_match_stem):
            dfs[stem] = len(set(map(by_lookup_match_piece, stem_matches)))
        # For each piece compute TF scores - Dictionary from piece to Dictionary from stem to count
        tfs = {}
        for piece, piece_matches in groupby(sorted(matches, key=by_lookup_match_piece), by_lookup_match_piece):
            tfs[piece] = {}
            for stem, stem_matches in groupby(sorted(piece_matches, key=by_lookup_match_stem), by_lookup_match_stem):
                tfs[piece][stem] = len(list(stem_matches))
        # Compute TF-IDF score
        return [ GraderResult(piece=piece, grade=sum([bm25_tf(cnt) * bm25_idf(number_of_pieces, dfs[stem]) for stem,cnt in piece_tfs.items() ]), meta={}) for piece, piece_tfs in tfs.items()]
    return bm25