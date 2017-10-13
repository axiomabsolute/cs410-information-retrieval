import itertools
from firms.models import flatten

# An stemmer is a function from snippet to a list of strings representing the index key
def get_pitches(snippet):
    return [
        [note.pitch.nameWithOctave] if note.isNote else
        [n.nameWithOctave for n in note.pitches] if note.isChord else
        ['rest%s' % note.duration.quarterLength]
        for note in snippet.notes
    ]

def index_key_by_pitch(snippet):
    return flatten([
        [
            ' '.join(line)
        ] for line in itertools.product(*get_pitches(snippet))
    ])

# Parm looks like [ [index_1_piece_1, index_2_piece_2, ...], [index_1_piece_2, index_2_piece_2, ...]... ]
# def merge_indexes_for_pieces(indexes_by_piece):
#     collected_indexes = zip(*indexes_by_piece)
#     return [ merge_indexes(index_collection) for index_collection in collected_indexes ]

# def make_indexes(index_methods, snippets_by_part):
#     print(snippets_by_part)
#     return [ [ Index(snippets, index_method, name) for name, index_method in index_methods.items() ] for snippets in snippets_by_part ]