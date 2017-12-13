from itertools import groupby
from operator import attrgetter, itemgetter
from abc import ABCMeta, abstractmethod
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
by_piece = itemgetter('piece')
by_piece_id = itemgetter('piece_id')
by_stem = itemgetter('stem')
by_lookup_match_piece = by(by_lookup_match, by_piece_id)
by_lookup_match_stem = by(by_lookup_match, by_stem)

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

def update_with(d1, d2, aggregator, zero):
    for k,v in d2.items():
        if k not in d1:
            d1[k] = zero()
        d1[k] = aggregator(d1[k], v)
    return d1

def update_with_sum(d1, d2):
    return update_with(d1, d2, lambda a,b: a+b, lambda: 0)

class Grader(metaclass=ABCMeta):
    def __init__(self):
        self.zero()

    @abstractmethod
    def zero(self):
        """
        Reset the grader's aggregator
        """
        pass

    @abstractmethod
    def grade(self, number_of_pieces):
        """
        Compute a grade based on the grader's current aggregator state
        """
        pass

    @abstractmethod
    def aggregate(self, matches):
        """
        Add a set of results to the grader's aggregator
        """
        pass

class Bm25Grader(Grader):
    def zero(self):
        self.tfs = {}
        self.dfs = {}
    
    def grade(self, number_of_pieces):
        tfs = self.tfs
        dfs = self.dfs
        return [ GraderResult(piece=piece, grade=sum([bm25_tf(cnt) * bm25_idf(number_of_pieces, dfs[stem]) for stem,cnt in piece_tfs.items() ]), meta={}) for piece, piece_tfs in tfs.items()]

    def aggregate(self, matches):
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

        # Merge existing with this iteration
        update_with_sum(self.dfs, dfs)
        for piece, piece_stems in tfs.items():
            if piece not in self.tfs:
                self.tfs[piece] = {}
            update_with_sum(self.tfs[piece], piece_stems)

class LogWeightedSumGrader(Grader):
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
