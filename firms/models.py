from collections import defaultdict
from functools import reduce


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

def get_part_details(pieces):
    """
    Gets a tuple of title, partName, and part for each part in a list of pieces
    """
    for piece in pieces:
        try:
            scores = [piece.getScoreByNumber(number) for number in piece.getNumbers()]
            for score in scores:
                for part in score.parts:
                    yield (score.metadata.title, part.partName, part)
        except:
            for part in piece.parts:
                yield (piece.metadata.title, part.partName, part)

def get_notes_and_rests(part):
    """
    Given a part, extracts a flattened list of all notes in the part
    part - the part to extract
    """
    return flatten([m.notesAndRests for m in part.measures(0, None) if m.isStream])

# When we get snippets, we need to account for chords. To handle this, treat each note value as a set and compute the cartesian
# product to produce all possible one-line snippets for the part
def get_snippets_for_piece(piece_name, part_name, notes, snippet_length):
    return [Snippet(piece_name, part_name, notes[i: i+snippet_length], i) for i in range(0, 1 + len(notes) - snippet_length)]

def get_snippets_for_parts(parts):
    return flatten(list((get_snippets_for_piece(part[0], part[1], get_notes_and_rests(part[2]), 5) for part in parts)))

def get_snippets_for_pieces(pieces):
    parts = list(get_part_details(pieces))
    return get_snippets_for_parts(parts)

class IRSystem:
    def __init__(self, index_methods, scorers = None, pieces = []):
        self.index_methods = index_methods
        parts = list(get_part_details(pieces))
        self.piece_names = set( (part[0] for part in parts) )
        # Break up pieces into a flat list of snippets
        snippets = get_snippets_for_parts(parts)
        # For each index_method, build an index
        self.indexes = { k:MemoryIndex(snippets, v, k) for k,v in index_methods.items() }
        # Store scorers
        self.scorers = scorers
                        
    def add_piece(self, piece):
        parts = get_part_details(piece)
        snippets = get_snippets_for_parts(parts)
        for snippet in snippets:
            for index in self.indexes.values():
                index.add_snippet(snippet)
        try:
            self.piece_names.add(piece.metadata.title)
        except:
            # Piece might not have title
            print("Piece does not have a title")
    
    def lookup(self, query):
        snippets_by_index_type = {index_name: index.lookup(query) for index_name,index in self.indexes.items()}
        return {scorer_name: scorer(snippets_by_index_type) for scorer_name,scorer in self.scorers.items()}
    
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

class MemoryIndex:
    def __init__(self, snippets, keyfn, name = ""):
        self.index = defaultdict(set)
        self.keyfn = keyfn
        self.name = name
        for snippet in snippets:
            self.add_snippet(snippet)
            
    def add_snippet(self, snippet):
        for key in self.keyfn(snippet):
            self.index[key].add(snippet)
            
    def lookup(self, query):
        return flatten([list(self.index[key]) for key in self.keyfn(query)])
    
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
    
def merge_indexes(indexes):
    return reduce(lambda x,y: x.merge_indexes(y), indexes)