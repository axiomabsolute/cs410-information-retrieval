import unittest
from music21 import converter

from firms.models import Snippet
from firms.stemmers import stem_by_normalized_rythm

QUARTER_RYTHM_LINE = "tinynotation: a b c d e"
VARIABLE_RYTHM_LINE = "tinynotation: a1 b4 c d e"

def build_simple_snippet(notes):
    return Snippet('test', 'test', notes, 0)

class TestStemByNormalizedRythm(unittest.TestCase):
    def setUp(self):
        self.QUARTER_RYTHM_LINE = build_simple_snippet(converter.parse(QUARTER_RYTHM_LINE).flat.notes)
        self.VARIABLE_RYTHM_LINE = build_simple_snippet(converter.parse(VARIABLE_RYTHM_LINE).flat.notes)

    def test_uniform_line(self):
        stemmed = stem_by_normalized_rythm(self.QUARTER_RYTHM_LINE)
        for stem in stemmed:
            for item in stem:
                self.assertEqual(item, 1.0)
    
    def test_VARIABLE_RYTHM_LINE(self):
        stemmed = stem_by_normalized_rythm(self.VARIABLE_RYTHM_LINE)
        expected = [ 1.0, 0.25, 0.25, 0.25, 0.25 ]
        for stem in stemmed:
            self.assertListEqual(stem, expected)

if __name__ == '__main__':
    unittest.main()