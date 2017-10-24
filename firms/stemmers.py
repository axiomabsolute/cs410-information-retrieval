"""
A stemmer is a function from a snippet to a list of strings, where each string represents a stemmed form of
the snippet. A stemming function may produce multiple stemmed forms for a given snippet.

Internally, most stemming functions work on either individual notes or pairwise between notes.
"""

from itertools import islice
from firms.models import flatten

def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def stringify_keys(key_list):
    return [ [str(item) for item in l] for l in key_list]

def join_stem_by_note(note_stems):
    return [ ' '.join(stem) for stem in note_stems ]

def stem_by_pitch(snippet):
    return [
        [note.pitch.nameWithOctave if note.isNote else
        "[ %s ]" % ' '.join([pitch.nameWithOctave for pitch in note.pitches])  if note.isChord else
        'rest'
        for note in snippet.notes]
    ]

def index_key_by_pitch(snippet):
    return join_stem_by_note(stem_by_pitch(snippet))

def stem_by_simple_pitch(snippet):
    return [
        [note.pitch.name if note.isNote else
        "[ %s ]" % ' '.join([pitch.name for pitch in note.pitches]) if note.isChord else
        'rest'
        for note in snippet.notes]
    ]

def index_key_by_simple_pitch(snippet):
    return join_stem_by_note(stem_by_simple_pitch(snippet))

def stem_by_rythm(snippet):
    return [
        [ note.duration.quarterLength for note in snippet.notes ]
    ]

def index_key_by_rythm(snippet):
    return join_stem_by_note(stringify_keys(stem_by_rythm(snippet)))

def stem_by_normalized_rythm(snippet):
    rythm_stems = stem_by_rythm(snippet)
    longest = max(flatten(rythm_stems))
    return [ [stem / longest for stem in rythm_stem] for rythm_stem in rythm_stems ]

def index_key_by_normalized_rythm(snippet):
    return join_stem_by_note(stringify_keys(stem_by_normalized_rythm(snippet)))