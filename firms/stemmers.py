"""
A stemmer is a function from a snippet to a list of strings, where each string represents a stemmed form of
the snippet. A stemming function may produce multiple stemmed forms for a given snippet.

Internally, most stemming functions work on either individual notes or pairwise between notes.
"""

def stem_by_pitch(snippet):
    return [
        [note.pitch.nameWithOctave if note.isNote else
        "[ %s ]" % ' '.join([pitch.nameWithOctave for pitch in note.pitches])  if note.isChord else
        'rest'
        for note in snippet.notes]
    ]

def index_key_by_pitch(snippet):
    return [ ' '.join(stem) for stem in stem_by_pitch(snippet) ]

def stem_by_simple_pitch(snippet):
    return [
        [note.pitch.name if note.isNote else
        "[ %s ]" % ' '.join([pitch.name for pitch in note.pitches]) if note.isChord else
        'rest'
        for note in snippet.notes]
    ]

def index_key_by_simple_pitch(snippet):
    return [ ' '.join(stem) for stem in stem_by_simple_pitch(snippet) ]

