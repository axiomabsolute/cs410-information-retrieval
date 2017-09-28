
# coding: utf-8

# # Outline of IR System
# 
# Components
# 1. Interface
# 2. Tokenizer
# 3. Indexer
# 4. Indexes
# 5. Scorer
# 6. Feedback

# In[1]:


from music21 import *


# In[2]:


# Models
from collections import defaultdict, Counter
from functools import reduce
import random

def flatten(l):
    return [item for sublist in l for item in sublist]

def get_parts_for_piece(piece):
    return piece.parts

def get_parts(pieces):
    for piece in pieces:
        try:
            scores = [piece.getScoreByNumber(number) for number in piece.getNumbers()]
            for score in scores:
                for part in score.parts:
                    yield (score.metadata.title, part.partName, part)
        except:
            for part in piece.parts:
                yield (piece.metadata.title, part.partName, part)

def get_notes(part):
    return flatten([m.notes for m in part.measures(0, None) if m.isStream])

# When we get snippets, we need to account for chords. To handle this, treat each note value as a set and compute the cartesian
# product to produce all possible one-line snippets for the part
def get_snippets_for_piece(piece_name, part_name, notes, snippet_length):
    return [Snippet(piece_name, part_name, notes[i: i+snippet_length], i) for i in range(0, 1 + len(notes) - snippet_length)]

def get_snippets_for_parts(parts):
    return flatten(list((get_snippets_for_piece(part[0], part[1], get_notes(part[2]), 5) for part in parts)))

def get_snippets_for_pieces(pieces):
    parts = list(get_parts(pieces))
    return get_snippets_for_parts(parts)

class IRSystem:
    def __init__(self, index_methods, scorers = None, pieces = []):
        self.index_methods = index_methods
        parts = list(get_parts(pieces))
        self.piece_names = set( (part[0] for part in parts) )
        # Break up pieces into a flat list of snippets
        snippets = get_snippets_for_parts(parts)
        # For each index_method, build an index
        self.indexes = { k:Index(snippets, v, k) for k,v in index_methods.items() }
        # Store scorers
        self.scorers = scorers
                        
    def add_piece(self, piece):
        parts = get_parts(pieces)
        snippets = get_snippets_for_parts(parts)
        for snippet in snippets:
            for index in self.indexes.values():
                index.add_snippet(snippet)
    
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
        
    def __repr__(self):
        return "Snippet(%s, %s, %s, %s)" % (self.piece, self.part, self.offset, [note.pitch.nameWithOctave for note in self.notes])

class Index:
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
        result = Index([], self.keyfn, self.name)
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
        #return "Index[%s]\n  %s" % (self.name, '\n  '.join(self.index.keys()))
    
def merge_indexes(indexes):
    return reduce(lambda x,y: x.merge_indexes(y), indexes)


# In[3]:


# Tokenizers
def wrap_query_as_piece(query):
    piece = stream.Score()
    part = stream.Part()
    part.partName = "query"
    measures = converter.parse("tinynotation: %s" % query)
    for measure in measures:
        part.append(measure)
    piece.append(part)
    return piece


# In[4]:


# Indexers
# An indexer is a function from snippet to a list of strings representing the index key
def get_pitches(snippet):
    return [note.pitch for note in snippet.notes]

def index_key_by_pitch(snippet):
    return [' '.join([pitch.nameWithOctave for pitch in get_pitches(snippet)])]

# Parm looks like [ [index_1_piece_1, index_2_piece_2, ...], [index_1_piece_2, index_2_piece_2, ...]... ]
def merge_indexes_for_pieces(indexes_by_piece):
    collected_indexes = zip(*indexes_by_piece)
    return [ merge_indexes(index_collection) for index_collection in collected_indexes ]

def make_indexes(index_methods, snippets_by_part):
    print(snippets_by_part)
    return [ [ Index(snippets, index_method, name) for name, index_method in index_methods.items() ] for snippets in snippets_by_part ]


# In[5]:


# Scorer
# A scorer is a function: Function[Dictionary[index_type, snippets], Dictionary[piece_name, number]

# Each time the query matches a snippet from a piece for each index, give it a score of 1, and sum them
def simple_sum_scorer(snippets_by_index_type):
    snippets = flatten(snippets_by_index_type.values())
    return Counter([snippet.piece for snippet in snippets])


# In[6]:


# Tests
shared_part_success = 'C4 D E8 F G16 A B c'
shared_part_failure = "c4 c'4 c''4 CC4 C4"
time_signature = '4/4'
tokenizer_test_query = '%s %s' % (time_signature, shared_part_success)
test_piece = "%s %s %s CC4 C4 c4" % (time_signature, shared_part_failure, shared_part_success)
test_piece_fail = "%s %s C4 c4" % (time_signature, shared_part_failure)

pieces = list((corpus.parse(piece) for piece in corpus.getComposer('bach')[:5]))

index_methods = {
    'By Pitch': index_key_by_pitch
}

scorer_methods = {
    'Simple Sum': simple_sum_scorer
}

def tokenizer_test(query, test_piece):
    query_piece = wrap_query_as_piece(query)
    test_piece = wrap_query_as_piece(test_piece)
    return (query_piece, test_piece)

def snippets_test(piece_name, piece, snippet_length = 5):
    parts = get_parts_for_piece(piece)
    snippets_by_part = [ get_snippets_for_piece(piece_name, part.partName, get_notes(part), snippet_length) for part in parts ]
    return snippets_by_part

#query_piece, test_piece = tokenizer_test(tokenizer_test_query, test_piece)
#test_piece_fail = wrap_query_as_piece(test_piece_fail)
#snippets_by_part = snippets_test("Test Piece", test_piece)
#fail_snippets_by_part = snippets_test("Fail Test Piece", test_piece_fail)
#merge_indexes_for_pieces(make_indexes(index_methods, flatten([snippets_by_part, fail_snippets_by_part])))


# In[7]:


irsystem = IRSystem(index_methods, scorer_methods, pieces)


# In[8]:


# Does not work in iPython
# pieces[1].show()


# In[9]:


all_snippets = get_snippets_for_pieces(pieces)
random_snippet = random.choice(all_snippets)
irsystem.lookup(random_snippet)


# In[17]:


random_snippets = random.sample(all_snippets, 20)
scores = [irsystem.lookup(s) for s in random_snippets]
list(zip(random_snippets, scores))


# In[ ]:




