import random
import datetime
from tabulate import tabulate
from music21 import corpus
from firms.graders import simple_sum_grader
from firms.stemmers import index_key_by_pitch
from firms.models import IRSystem, get_snippets_for_pieces

def print_timing(message):
    print("%s %s" % (datetime.datetime.utcnow(), message))

print()
print_timing("Loading pieces")
piece_paths = corpus.getComposer('bach')
pieces = (corpus.parse(piece) for piece in piece_paths)

index_methods = {
    'By Pitch': index_key_by_pitch
}

scorer_methods = {
    'Simple Sum': simple_sum_grader
}

print_timing("Building IR system")
irsystem = IRSystem(index_methods, scorer_methods, pieces)

print_timing("Sampling snippets for demonstration")
sample_pieces = (corpus.parse(piece) for piece in random.sample(piece_paths, min(5, len(piece_paths))))
random_snippets = random.sample(list(get_snippets_for_pieces(sample_pieces)), 20)
scores = [irsystem.lookup(s) for s in random_snippets]
scored_snippets = zip(random_snippets, scores)

print_timing("Printing results")
print("==========================================================================")
table_headers = ['Query Source', 'Query Line', 'Grading Method', 'Piece', 'Grade']
table_rows = []
for (snippet, scores) in scored_snippets:
    for (scorer, score) in scores.items():
        for (matching_piece, grade) in score.items():
            table_rows.append([
                "%s %s (m %s)" % (snippet.piece, snippet.part, snippet.offset),
                ' '.join(snippet.simple_line()),
                scorer,
                matching_piece,
                grade
            ])
table_rows.sort(key=lambda x: (x[0], x[2], -1*x[4]))
print(tabulate(table_rows, headers=table_headers))

input("\nDone - press enter to exit.")