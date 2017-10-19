from collections import defaultdict
from functools import reduce
from abc import ABCMeta, abstractmethod
import datetime

import music21

def print_timing(message, tabcount=0):
    print("\t" * tabcount + "%s %s" % (datetime.datetime.utcnow(), message))

def flatten(toflatten):
    """
    Flattens nested iterable by one level
    toflatten - the list to flatten
    """
    return [item for sublist in toflatten for item in sublist]

def get_parts_for_piece(piece):
    """
    Returns all parts for a piece
    piece - the piece to extract
    """
    return piece.parts

def get_part_details(piece):
    """
    Gets a tuple of title, partName, and part for each part in a list of pieces
    """
    try:
        scores = [piece.getScoreByNumber(number) for number in piece.getNumbers()]
        for score in scores:
            for part in score.parts:
                yield (score.metadata.title, part.partName, part)
    except:
        for idx,part in enumerate(piece.parts):
            yield (piece.metadata.title, part.partName or "Part %s" % idx, part)

def get_notes_and_rests(part):
    """
    Given a part, extracts a flattened list of all notes in the part
    part - the part to extract
    """
    return flatten([m.notesAndRests for m in part.measures(0, None) if m.isStream])

# When we get snippets, we need to account for chords. To handle this, treat each note value as a set and compute the cartesian
# product to produce all possible one-line snippets for the part
def get_snippets_for_piece(piece_name, part_name, notes, snippet_length):
    return (Snippet(piece_name, part_name, notes[i: i+snippet_length], i) for i in range(0, 1 + len(notes) - snippet_length))

def get_snippets_for_part(part):
    return get_snippets_for_piece(part[0], part[1], get_notes_and_rests(part[2]), 5)

def get_snippets_for_parts(parts):
    for snippets_by_part in (get_snippets_for_piece(part[0], part[1], get_notes_and_rests(part[2]), 5) for part in parts):
        for snippet in snippets_by_part:
            yield snippet

def get_snippets_for_pieces(pieces):
    parts = (part for piece in pieces for part in get_part_details(piece))
    return get_snippets_for_parts(parts)

class IRSystem(metaclass=ABCMeta):
    def __init__(self, index_methods, scorers, piece_paths):
        self.index_methods = index_methods
        self.scorers = scorers
        self.indexes = {k:self.makeEmptyIndex(v,k) for k,v in index_methods.items()}
        for piece_path in piece_paths:
            print_timing("Processing %s" % piece_path, 1)
            piece = music21.corpus.parse(piece_path)
            self.add_piece(piece, piece_path)

    @abstractmethod
    def add_piece(self, piece, piece_path): pass

    @abstractmethod
    def makeEmptyIndex(self, indexfn, name): pass

    def lookup(self, snippet):
        snippets_by_index_type = {index_name: index.lookup(snippet) for index_name,index in self.indexes.items()}
        return {scorer_name: scorer(snippets_by_index_type) for scorer_name,scorer in self.scorers.items()}

    def query(self, query):
        queryStream = music21.tinyNotation.Converter.parse(query)
        queryPart = ("query", "query", queryStream)
        querySnippets = get_snippets_for_part(queryPart)
        snippets_by_index_type = {index_name: flatten((index.lookup(snippet) for snippet in querySnippets)) for index_name,index in self.indexes.items()}
        return {scorer_name: scorer(snippets_by_index_type) for scorer_name,scorer in self.scorers.items()}

class MemoryIRSystem(IRSystem):
    def __init__(self, index_methods, scorers = None, piece_paths = []):
        self.piece_names = {}
        super().__init__(index_methods, scorers, piece_paths)

    def makeEmptyIndex(self, indexfn, name):
        return MemoryIndex([], indexfn, name)
    
    def add_piece(self, piece, piece_path):
        for part in get_part_details(piece):
            self.piece_names[part[0]] = piece_path
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
    def lookup(self, query):
        pass

class MemoryIndex(FirmIndex):
    def __init__(self, snippets, keyfn, name = ""):
        super().__init__(snippets, keyfn, name)
            
    def add_snippet(self, snippet):
        for key in self.keyfn(snippet):
            self.index[key].add(snippet)

    def lookup(self, query):
        return flatten([self.index[key] for key in self.keyfn(query)])
    
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
    