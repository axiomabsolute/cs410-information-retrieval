"""
A stemmer is a function from a snippet to a list of strings, where each string represents a stemmed form of
the snippet. A stemming function may produce multiple stemmed forms for a given snippet.

Internally, most stemming functions work on either individual notes or pairwise between notes.
"""

from itertools import islice, chain
from operator import itemgetter
from firms.models import flatten
from music21.interval import Interval
from music21.chord import Chord

def window(seq, window_size=2):
    """
    Returns a sliding window (of width n) over data from the iterable"
       s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...
    arguments:
    seq         the sequence to window over
    window_size the size of the windows
    """
    iterator = iter(seq)
    result = tuple(islice(iterator, window_size))
    if len(result) == window_size:
        yield result
    for elem in iterator:
        result = result[1:] + (elem,)
        yield result

def get_number_of_voices(gnote):
    return len(gnote.pitches)

def split_voices(lead, current):
    num_lead = get_number_of_voices(lead)
    num_current = get_number_of_voices(current)
    if num_lead == num_current:
        return current.pitches
    middle = [sorted([ (c, abs(Interval(e,c).cents)) for c in current ], key=itemgetter(1))[0] for e in lead.pitches[1:-1]]
    return list(chain(current.pitches[0:1], middle, current.pitches[-1:]))

def split_voice_lines(indexed_notes):
    """
    Split potentially polyphonic line into multiple monophonic lines using voice leading

    indexed_notes   List of tuples of the form (position, GeneralNote)
    
    returns         List of lists of tuples of the form (position, Note)
    """
    max_number_of_voices = max(get_number_of_voices(note) for idx,note in indexed_notes)
    peak = [i for i,(idx,note) in enumerate(indexed_notes) if get_number_of_voices(note) == max_number_of_voices][0]

    head = indexed_notes[:peak+1][::-1]
    climb = []
    if len(head) > 1:
        lead = head[0][1]
        for i,n in head[1:]:
            split_result = split_voices(lead, n)
            climb.append( (i, split_result) )
            lead = n
    
    tail = indexed_notes[peak:]
    fall = []
    if len(tail) > 1:
        lead = tail[0][1]
        for i,n in tail[1:]:
            split_result = split_voices(lead, n)
            fall.append(split_results)
            lead = n

    results = []
    for i in range(max_number_of_voices):
        results.append([])
    
    for i,voices in climb:
        for j,voice in enumerate(voices):
            results[j].append( (i,voice) )
    for i,voices in fall:
        for j,voice in enumerate(fall):
            results[j].append( (i,voice) )
    for result in results:
        result.append(indexed_notes[peak])

    return results
    
def get_voice_lines(notes):
    """
    Breaks up a stream of potentially polyphonic notes into one or more monophonic (or unphonated) voices
    notes   stream of GeneralNote objects
    """
    # If everything is a rest, just wrap the line in a list and return as is
    if all(note.isRest for note in notes):
        return [notes]
    indexed_notes = list(enumerate(notes))
    indexed_non_rests = [(idx,note) for idx,note in indexed_notes if not note.isRest]
    indexed_rests = [(idx,note) for idx,note in indexed_notes if note.isRest]

    # Do voice leading IGNORING rests
    # List[ List[ (idx, note.Note) ] ]
    raw_voice_lines = split_voice_lines(indexed_non_rests)

    # Mix the rests back in
    voice_lines = []
    for rvl in raw_voice_lines:
        with_rests = chain(rvl, indexed_rests)
        ordered = sorted(with_rests, key=itemgetter(0))
        without_idx = [o[1] for o in ordered]
        voice_lines.append(without_idx)

    return voice_lines

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
    if longest == 0:
        longest = 1.0
    return [ [stem / longest for stem in rythm_stem] for rythm_stem in rythm_stems ]

def index_key_by_normalized_rythm(snippet):
    return join_stem_by_note(stringify_keys(stem_by_normalized_rythm(snippet)))