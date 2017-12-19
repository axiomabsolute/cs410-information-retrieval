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
from music21.note import Note

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
    """
    Given two sequential notes, if the lead note contains more voices than current, then duplicate
    the notes in current to match lead, producing continuous voice lines
        :param lead: Leading note
        :param current: Current node
    """
    num_lead = get_number_of_voices(lead)
    num_current = get_number_of_voices(current)
    if current.isNote:
        return [ Note(current.pitch, quarterLength=current.duration.quarterLength) for i in range(num_lead) ]
    if num_lead == num_current:
        return [ Note(pitch, quarterLength=current.duration.quarterLength) for pitch in current.pitches]
    if current.isChord and len(current.pitches) == 0:
        raise RuntimeError("The system was able to parse the file, but detected an illegal construct: empty chord")
    middle = map(itemgetter(0), [sorted([ (c, abs(Interval(e,c).cents)) for c in current.pitches ], key=itemgetter(1))[0] for e in lead.pitches[1:-1]])
    return [ Note(pitch, quarterLength=current.duration.quarterLength) for pitch in chain(current.pitches[0:1], middle, current.pitches[-1:])]

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
            lead = Chord(split_result)
    
    tail = indexed_notes[peak:]
    fall = []
    if len(tail) > 1:
        lead = tail[0][1]
        for i,n in tail[1:]:
            split_result = split_voices(lead, n)
            fall.append( (i, split_result) )
            lead = Chord(split_result)

    results = []

    for i in range(max_number_of_voices):
        results.append([])

    source_idx_for_peak,peak_note = indexed_notes[peak]
    for i,result in enumerate(results):
        for j,voices in climb:
            result.append( (j, voices[i]) )
        for j,voices in fall:
            result.append( (j, voices[i]) )
        result.append( (source_idx_for_peak, Note(peak_note.pitches[i], quarterLength=peak_note.duration.quarterLength) ) )

    return results
    
def get_voice_lines(notes):
    """
    Breaks up a stream of potentially polyphonic notes into one or more monophonic (or unphonated) voices
    notes   stream of GeneralNote objects
    """
    # If everything is a rest, just wrap the line in a list and return as is
    if all(note.isRest or note.isNote for note in notes):
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

def get_contour(note1, note2):
    if note1.isRest and note2.isRest:
        return 's'
    elif note1.isRest and not note2.isRest:
        return 'u'
    elif not note1.isRest and note2.isRest:
        return 'd'
    else:
        interval = Interval(note1, note2)
        cents = interval.cents
        if cents == 0:
            return 's'
        if cents > 0:
            return 'u'
        return 'd'

def get_interval(note1, note2):
    if note1.isRest or note2.isRest:
        return 'rest'
    return str(Interval(note1, note2).cents)

def stringify_keys(key_list):
    """
    Transform a list of stem keys into a list of string keys for persistence
        :param key_list: List of stem keys
    """
    return [ [str(item) for item in l] for l in key_list]

def join_stem_by_note(note_stems):
    return [ ' '.join(stem) for stem in note_stems ]

def stem_by_pitch(snippet):
    voices = get_voice_lines(snippet.notes)
    return [
        [note.pitch.nameWithOctave if note.isNote else
        "[ %s ]" % ' '.join([pitch.nameWithOctave for pitch in note.pitches])  if note.isChord else
        'rest'
        for note in voice] for voice in voices
    ]

def index_key_by_pitch(snippet):
    return join_stem_by_note(stem_by_pitch(snippet))

def stem_by_simple_pitch(snippet):
    voices = get_voice_lines(snippet.notes)
    return [
        [note.pitch.name if note.isNote else
        "[ %s ]" % ' '.join([pitch.name for pitch in note.pitches]) if note.isChord else
        'rest'
        for note in voice]for voice in voices
    ]

def index_key_by_simple_pitch(snippet):
    return join_stem_by_note(stem_by_simple_pitch(snippet))

def stem_by_interval(snippet):
    voices = get_voice_lines(snippet.notes)
    return [
        [
            get_interval(*pair) for pair in window(voice)
        ] for voice in voices
    ]

def index_key_by_interval(snippet):
    return join_stem_by_note(stem_by_interval(snippet))

def stem_by_contour(snippet):
    voices = get_voice_lines(snippet.notes)
    return [
        [
            get_contour(*pair) for pair in window(voice)
        ] for voice in voices
    ]

def index_key_by_contour(snippet):
    return join_stem_by_note(stem_by_contour(snippet))

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