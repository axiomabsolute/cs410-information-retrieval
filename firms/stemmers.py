import itertools
from firms.models import flatten

# An stemmer is a function from snippet to a list of strings representing the index key
def get_pitches(snippet):
    return [
        [note.pitch.nameWithOctave] if note.isNote else
        [ "[ %s ]" % ' '.join([pitch.nameWithOctave for pitch in note.pitches]) ] if note.isChord else
        ['rest%s' % note.duration.quarterLength]
        for note in snippet.notes
    ]

def index_key_by_pitch(snippet):
    return flatten([
        [
            ' '.join(line)
        ] for line in itertools.product(*get_pitches(snippet))
    ])
