"""
Implementations of FIRMS Grader abstract class
"""

from itertools import groupby
from operator import attrgetter, itemgetter
from math import log
from firms.models import Grader, GraderResult

def by(*getters):
    """
    Chain getters. by(a, b) means
    "Get a, then get b from the result of a"
        :param *getters: Getters to chain
    """
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
by_piece = itemgetter('piece')
by_piece_id = itemgetter('piece_id')
by_stem = itemgetter('stem')
by_lookup_match_piece = by(by_lookup_match, by_piece_id)
by_lookup_match_stem = by(by_lookup_match, by_stem)

def bm25_idf(N, df):
    """
    Compute BM25 inverse document frequency
        :param N: Number of documents
        :param df: Document frequency
    """
    assert(N >= df)
    return log( (N - df + 0.5) / (df + 0.5) )

def bm25_tf(tf, k=1.2):
    """
    Compute BM25 Term frequency, without document length normalization
        :param tf: Term frequency
        :param k=1.2: K parameter
    """
    return (tf * (k + 1) )/(tf + k)

def update_with(d1, d2, aggregator, zero):
    """
    Fold the right dictionary into the left.
    This is a mutating function
        :param d1: Dictionary to fold into
        :param d2: Dictionary draw updates from
        :param aggregator: Definition of how to update d1
        :param zero: What to do if a key in d2 isn't in d1
    """
    for k, v in d2.items():
        if k not in d1:
            d1[k] = zero()
        d1[k] = aggregator(d1[k], v)
    return d1

def update_with_union(d1, d2):
    """
    Update dictionary with sets as values by unioning
        :param d1: Set to fold into
        :param d2: Set to fold from
    """
    return update_with(d1,d2, lambda a,b: a.union(b), set)

def update_with_sum(d1, d2):
    """
    Update dictionary with numeric values by summing
        :param d1: Dictionary to fold into
        :param d2: Dictionary to fold from
    """
    return update_with(d1, d2, lambda a,b: a+b, lambda: 0)

class Bm25Grader(Grader):
    """
    Implementation of FIRMS grader as Oakpi BM25 without document length normalization
        :param Grader: FIRMS Grader abstract class
    """
    def zero(self):
        self.tfs = {}
        self.dfs = {}
    
    def grade(self, number_of_pieces):
        tfs = self.tfs
        dfs = self.dfs
        return [ GraderResult(piece=piece, grade=sum([bm25_tf(cnt) * bm25_idf(number_of_pieces, len(dfs[stem])) for stem,cnt in piece_tfs.items() ]), meta={}) for piece, piece_tfs in tfs.items()]

    def aggregate(self, matches):
        # Compute DF - Dictionary from stem -> piece count
        dfs = {}
        for stem, stem_matches in groupby(sorted(matches, key=by_lookup_match_stem), by_lookup_match_stem):
            dfs[stem] = set(map(by_lookup_match_piece, stem_matches))

        # For each piece compute TF scores - Dictionary from piece to Dictionary from stem to count
        tfs = {}
        for piece, piece_matches in groupby(sorted(matches, key=by_lookup_match_piece), by_lookup_match_piece):
            tfs[piece] = {}
            for stem, stem_matches in groupby(sorted(piece_matches, key=by_lookup_match_stem), by_lookup_match_stem):
                tfs[piece][stem] = len(list(stem_matches))

        # Merge existing with this iteration
        update_with_union(self.dfs, dfs)
        for piece, piece_stems in tfs.items():
            if piece not in self.tfs:
                self.tfs[piece] = {}
            update_with_sum(self.tfs[piece], piece_stems)

class LogWeightedSumGrader(Grader):
    """
    Implementation of FIRMS Grader as a weighted sum of log counts
        :param Grader: FIRMS Grader abstract class
    """
    def __init__(self, weights):
        self.weights = weights
        super().__init__()

    def zero(self):
        self.stemmer_counts_by_piece = {}
    
    def grade(self, number_of_pieces):
        grades = []
        for piece, stemmer_counts in self.stemmer_counts_by_piece.items():
            piece_grade = 0
            for stemmer, count in stemmer_counts.items():
                piece_grade = piece_grade + ( self.weights[stemmer] * log(count))
            grades.append( GraderResult(piece=piece, grade=piece_grade, meta={}) )
        return grades
    
    def aggregate(self, matches):
        for piece, piece_matches in groupby(sorted(matches, key=by_lookup_match_piece), by_lookup_match_piece):
            if piece not in self.stemmer_counts_by_piece:
                self.stemmer_counts_by_piece[piece] = {}
            for stemmer, stemmer_matches in groupby(sorted(piece_matches, key=by_stemmer), by_stemmer):
                if stemmer not in self.stemmer_counts_by_piece[piece]:
                    self.stemmer_counts_by_piece[piece][stemmer] = 0
                self.stemmer_counts_by_piece[piece][stemmer] = self.stemmer_counts_by_piece[piece][stemmer] + len(list(stemmer_matches))
