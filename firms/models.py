from collections import defaultdict, namedtuple
from functools import reduce
from abc import ABCMeta, abstractmethod
import datetime

import music21

LookupMatch = namedtuple('LookupMatch', ['id', 'piece', 'part', 'offset', 'stem'])
GraderMatch = namedtuple('GraderMatch', ['stemmer', 'lookup_match'])
GraderResult = namedtuple('GraderResult', ['piece', 'grade', 'meta'])

def print_timing(message, tabcount=0):
    print("\t" * tabcount + "%s %s" % (datetime.datetime.utcnow(), message))

def flatten(toflatten):
    """
    Flattens nested iterable by one level
    toflatten - the list to flatten
    """
    return [item for sublist in toflatten for item in sublist]

def get_part_details(piece):
    """
    Gets a tuple of title, partName, and part for each part in a list of pieces
    """
    piece_title = piece.metadata.title
    for idx,part in enumerate(piece.recurse().parts):
        yield Part(piece_title, part.partName or "Part %s" % idx, part)

def get_notes_and_rests(part):
    """
    Given a part, extracts a flattened list of all notes in the part
    part - the part to extract
    """
    return list(part.recurse().notesAndRests)

def get_snippets_for_piece(piece_name, part_name, notes, snippet_length):
    return (Snippet(piece_name, part_name, notes[i: i+snippet_length], i) for i in range(0, 1 + len(notes) - snippet_length))

def get_snippets_for_part(part):
    return get_snippets_for_piece(part.piece, part.name, get_notes_and_rests(part.part), 5)

class IRSystem(metaclass=ABCMeta):
    def __init__(self, index_methods, scorers, piece_paths, rebuild=True):
        self.index_methods = index_methods
        self.scorers = scorers
        self.indexes = {k:self.makeEmptyIndex(v,k) for k,v in index_methods.items()}
        total_pieces = len(piece_paths)
        if rebuild:
            for idx,piece_path in enumerate(piece_paths):
                print_timing("Processing %s of %s - %s" % (1+idx, total_pieces, piece_path), 1)
                piece = music21.corpus.parse(piece_path)
                self.add_piece(piece, piece_path)

    @abstractmethod
    def add_piece(self, piece, piece_path): pass

    @abstractmethod
    def makeEmptyIndex(self, indexfn, name): pass

    def lookup(self, snippet, *args):
        snippets_by_index_type = {index_name: index.lookup(snippet, *args) for index_name,index in self.indexes.items()}
        return {scorer_name: scorer(snippets_by_index_type) for scorer_name,scorer in self.scorers.items()}

    @abstractmethod
    def corpus_size(self): pass

    def raw_query(self, query, *args):
        queryStream = None
        try:
            assert('Stream' in query.classSet or 'StreamIterator' in query.classSet)
            queryStream = query
        except:
            queryStream = music21.tinyNotation.Converter.parse(query)
        queryPart = Part("query", "query", queryStream)
        # This needs to be a list because it gets iterated over for every index type
        querySnippets = list(get_snippets_for_part(queryPart))
        snippets_by_index_type = []
        for index_name,index in self.indexes.items():
            for snippet in querySnippets:
                lookup_results = index.lookup(snippet, *args)
                for lookup_result in lookup_results:
                    snippets_by_index_type.append( GraderMatch(stemmer=index_name, lookup_match=lookup_result) )
        return snippets_by_index_type

    def query(self, query, *args):
        corpus_size = self.corpus_size()
        snippets_by_index_type = self.raw_query(query, *args)
        scores_by_scorer = {scorer_name: scorer(snippets_by_index_type, corpus_size) for scorer_name,scorer in self.scorers.items()}
        return scores_by_scorer

class MemoryIRSystem(IRSystem):
    def __init__(self, index_methods, scorers = None, piece_paths = []):
        self.piece_names = {}
        super().__init__(index_methods, scorers, piece_paths)

    def corpus_size(self):
        return len(self.piece_names())

    def makeEmptyIndex(self, indexfn, name):
        return MemoryIndex([], indexfn, name)
    
    def add_piece(self, piece, piece_path):
        for part in get_part_details(piece):
            self.piece_names[part.piece] = piece_path
            snippets = get_snippets_for_part(part)
            for idx in self.indexes.values():
                for snippet in snippets:
                    idx.add_snippet(snippet)
    
    def __repr__(self):
        return "IRSystem(%s pieces)" % (len(self.piece_names))
                        
class Snippet:
    def __init__(self, piece_name, part, notes, offset):
        self.piece = piece_name
        self.part = part
        self.notes = notes
        self.offset = offset
    
    def simple_line(self):
        return [
            note.pitch.nameWithOctave if note.isNote else
            '[%s]' % ' '.join([pitch.nameWithOctave for pitch in note.pitches]) if note.isChord else
            'rest%s' % note.duration.quarterLength
            for note in self.notes
        ]
        
    def __repr__(self):
        return "Snippet(%s, %s, %s, %s)" % (self.piece, self.part, self.offset, self.simple_line())

class Part:
    def __init__(self, piece, name, part):
        self.piece = piece
        self.name = name
        self.part = part

class FirmIndex(metaclass=ABCMeta):
    def __init__(self, snippets, keyfn, name = ""):
        self.index = defaultdict(set)
        self.keyfn = keyfn
        self.name = name
        for snippet in snippets:
            self.add_snippet(snippet)

    @abstractmethod
    def add_snippet(self, snippet, *args):
        pass

    @abstractmethod
    def lookup(self, snippet, *args):
        pass

class MemoryIndex(FirmIndex):
    def __init__(self, snippets, keyfn, name = ""):
        super().__init__(snippets, keyfn, name)
            
    def add_snippet(self, snippet):
        for key in self.keyfn(snippet):
            self.index[key].add(snippet)

    def lookup(self, snippet):
        return flatten([self.index[key] for key in self.keyfn(snippet)])
    
    def merge_indexes(self, index):
        result = MemoryIndex([], self.keyfn, self.name)
        for k,v in self.index.items():
            for item in v:
                result.index[k].add(item)
        for k,v in index.index.items():
            for item in v:
                result.index[k].add(item)
        return result
    
    def __repr__(self):
        result = "Index[%s]\n" % self.name
        for key, values in self.index.items():
            result += "  %s - %s\n" % (key, len(values))
        return result
    