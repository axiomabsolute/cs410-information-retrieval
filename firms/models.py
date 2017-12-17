"""
Collection of models and functions for interacting with them.
"""

from collections import defaultdict, namedtuple
from abc import ABCMeta, abstractmethod
import os

import music21

# A part of a musical score, represented by a music21 stream
# and lineage information
Part = namedtuple('Part', ['piece', 'name', 'part'])

# A single query match row
LookupMatch = namedtuple('LookupMatch', [
    'id', 'piece', 'part', 'offset', 'stem', 'path', 'piece_id'
])

# A LookupMatch and the stemmer name that caused the match
GraderMatch = namedtuple('GraderMatch', ['stemmer', 'lookup_match'])

# A single result from grading a piece
GraderResult = namedtuple('GraderResult', ['piece', 'grade', 'meta'])

def flatten(toflatten):
    """
    Flattens nested iterable by one level
        :param toflatten: Sequence of nested sequences to flatten
    """
    return [item for sublist in toflatten for item in sublist]

def get_part_details(general_stream):
    """
    Gets a tuple of title, partName, and part for each part in a list of pieces
    """
    for piece in general_stream.recurse(classFilter=music21.stream.Score, skipSelf=False):
        piece_title = (piece and piece.metadata and piece.metadata.title) or "Untitled"
        for idx, part in enumerate(piece.recurse().parts):
            yield Part(piece_title, part.partName or "Part %s" % idx, part)

def get_notes_and_rests(part):
    """
    Given a part, extracts a flattened list of all notes in the part
    part - the part to extract
    """
    return list(part.recurse().notesAndRests)

def get_snippets_for_piece(piece_name, part_name, notes, snippet_length):
    """
    Generate a sequence of all snippets from a flat sequence of notes
        :param piece_name: Name of the source piece
        :param part_name: Name of the source part
        :param notes: Seq of notes
        :param snippet_length: Desired length of each snippet
    """
    return (Snippet(piece_name, part_name, notes[i: i+snippet_length], i) for i in range(0, 1 + len(notes) - snippet_length))

def get_snippets_for_part(part, explicit_repeats=False):
    """
    Generate all snippets for a part
    Can expand repeated sections by converting the part to MIDI and back. May be slow.
        :param part: The music21 part to generate snippets from
        :param explicit_repeats=False: Flag controlling whether repeated sections are expanded
    """
    if explicit_repeats:
        try:
            tmpfilename = 'tmpremoveme.mid'
            part.part.write("midi", tmpfilename)
            newstream = music21.converter.parse(tmpfilename)
            os.remove(tmpfilename)
            print("\t\tSuccessfully converted explicit repeats")
            return get_snippets_for_piece(part.piece, part.name, get_notes_and_rests(newstream), 5)
        except Exception:
            print("\t\tUnable to convert to midi and back. Falling back to default form.")
    return get_snippets_for_piece(part.piece, part.name, get_notes_and_rests(part.part), 5)

class IRSystem(metaclass=ABCMeta):
    """
    A complete IR system that defines operations in terms of abstract FirmsIndex instances
        :param metaclass=ABCMeta: Abstract MetaClass
    """
    def __init__(self, index_methods, graders, piece_paths, rebuild=True):
        """
        Constructor
            :param self:
            :param index_methods: Dictionary of stemmers
            :param graders: Dictionary of graders
            :param piece_paths: List of file paths to pieces
            :param rebuild=True: Boolean flag erases existing FIRMS index if true
        """
        self.index_methods = index_methods
        self.grader_methods = graders
        self.indexes = {k:self.make_empty_index(v, k) for k, v in index_methods.items()}
        if rebuild:
            for idx, piece_path in enumerate(piece_paths):
                print("Adding piece #%s: %s" % (idx, piece_path))
                piece = music21.corpus.parse(piece_path)
                self.add_piece(piece, piece_path)

    @abstractmethod
    def add_piece(self, piece, piece_path):
        """
        Add a single piece to FIRMS
            :param self:
            :param piece: Music21 stream representing the piece
            :param piece_path: Original path to the piece
        """
        pass

    @abstractmethod
    def make_empty_index(self, indexfn, name):
        """
        Create a new, empty
            :param self:
            :param indexfn: Function defining how a single snippet is indexed
            :param name: Name of the indexing method
        """
        pass

    def lookup(self, snippet, *args):
        """
        Lookup a single snippet
            :param self:
            :param snippet: Music21 stream representing the snippet
            :param *args: Additional arguments, passed on to individual index lookups
        """
        snippets_by_index_type = {index_name: index.lookup(snippet, *args) for index_name, index in self.indexes.items()}
        return {scorer_name: scorer(snippets_by_index_type) for scorer_name, scorer in self.grader_methods.items()}

    @abstractmethod
    def corpus_size(self):
        """
        Returns the number of pieces in FIRMS instance
            :param self:
        """
        pass

    def raw_query(self, query, *args):
        """
        Perform a query without aggregating and grading results
            :param self:
            :param query: Query represented by a Music21 stream
            :param *args: Extra arguments passed on to index lookup methods
        """
        for grader in self.grader_methods.values():
            grader.zero()
        query_stream = None
        try:
            assert 'Stream' in query.classSet or 'StreamIterator' in query.classSet
            query_stream = query
        except AssertionError:
            query_stream = music21.tinyNotation.Converter.parse(query)
        query_part = Part("query", "query", query_stream)
        # This needs to be a list because it gets iterated over for every index type
        query_snippets = list(get_snippets_for_part(query_part))
        for index_name, index in self.indexes.items():
            for snippet in query_snippets:
                lookup_results = index.lookup(snippet, *args)
                for grader in self.grader_methods.values():
                    grader.aggregate([GraderMatch(stemmer=index_name, lookup_match=lookup_result) for lookup_result in lookup_results])

    def query(self, query, *args):
        """
        Perform a query, aggregate, and rank results
            :param self:
            :param query: Query represented by Music21 stream
            :param *args: Additional args passed on to raw_query, then to individual index queries
        """
        corpus_size = self.corpus_size()
        self.raw_query(query, *args)
        grades_by_grader = {grader_name: grader.grade(corpus_size) for grader_name, grader in self.grader_methods.items()}
        return grades_by_grader

class Snippet:
    """
    Represents a short snippet of a musical work as a list of note values, along with lineage
    information for piece and part.
    """
    def __init__(self, piece_name, part, notes, offset):
        """
        Constructor
            :param self:
            :param piece_name: Name of the originating piece
            :param part: Name of the originating part
            :param notes: List of music21 notes
            :param offset: Number of notes offset from the start of the part
        """
        self.piece = piece_name
        self.part = part
        self.notes = notes
        self.offset = offset
    
    def simple_line(self):
        """
        Returns a simplified string representation of the pitches of notes in a snippet.
        Used for debugging
            :param self:
        """
        return [
            note.pitch.nameWithOctave if note.isNote else
            '[%s]' % ' '.join([pitch.nameWithOctave for pitch in note.pitches]) if note.isChord else
            'rest%s' % note.duration.quarterLength
            for note in self.notes
        ]
        
    def __repr__(self):
        """
        String representation, based on simple_line and properties
            :param self:
        """
        return "Snippet(%s, %s, %s, %s)" % (self.piece, self.part, self.offset, self.simple_line())

class FirmIndex(metaclass=ABCMeta):
    """
    A single stemming method
        :param metaclass=ABCMeta: Abscract MetaClass
    """
    def __init__(self, snippets, keyfn, name = ""):
        """
        Constructor
            :param self:
            :param snippets: List of snippets to add to index
            :param keyfn: Stemming method
            :param name="": Name of the stemming method
        """
        self.index = defaultdict(set)
        self.keyfn = keyfn
        self.name = name
        for snippet in snippets:
            self.add_snippet(snippet)

    @abstractmethod
    def add_snippet(self, snippet, *args):
        """
        Add a single snippet to the index
            :param self:
            :param snippet: Snippet to add
            :param *args: Arbitrary additional arguments
        """
        pass

    @abstractmethod
    def lookup(self, snippet, *args):
        """
        Look up a single snippet and return a list of LookupMatch tuples
            :param self:
            :param snippet: Snippet to lookup
            :param *args: Arbitrary extra args
        """
        pass

class Grader(metaclass=ABCMeta):
    """
    An implementation of a LookupMatch aggregation, grading, and ranking method.
    This is a *stateful* object, allowing results to be incrementally collected
    before aggregation.
        :param metaclass=ABCMeta: Abstract MetaClass
    """
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
        Compute grades for the pieces currently stored
            :param self:
            :param number_of_pieces: The total number of pieces in the corpus
        """
        pass

    @abstractmethod
    def aggregate(self, matches):
        """
        Add a set of results to the grader's aggregator
            :param self:
            :param matches: List of LookupMatch tuples to add to the aggregator
        """
        pass
