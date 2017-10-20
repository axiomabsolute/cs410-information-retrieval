import random
from tabulate import tabulate
from music21 import corpus
from firms.graders import simple_sum_grader
from firms.stemmers import index_key_by_pitch, index_key_by_simple_pitch
from firms.models import MemoryIRSystem, get_snippets_for_pieces, print_timing
from firms.sql_irsystems import SqlIRSystem

print()
print_timing("Loading pieces")
piece_paths = corpus.getComposer('bach')[:100]

index_methods = {
    'By Pitch': index_key_by_pitch,
    'By Simple Pitch': index_key_by_simple_pitch
}

scorer_methods = {
    'Simple Sum': simple_sum_grader
}

print_timing("Building IR system")
# irsystem = MemoryIRSystem(index_methods, scorer_methods, piece_paths)

# print_timing("Sampling snippets for demonstration")
# sample_pieces = (corpus.parse(piece) for piece in random.sample(piece_paths, min(5, len(piece_paths))))
# random_snippets = random.sample(list(get_snippets_for_pieces(sample_pieces)), 20)
# scores = [irsystem.lookup(s) for s in random_snippets]
# scored_snippets = zip(random_snippets, scores)

# print_timing("Printing results")
# print("==========================================================================")
# table_headers = ['Query Source', 'Query Line', 'Grading Method', 'Piece', 'Grade']
# table_rows = []
# for (snippet, scores) in scored_snippets:
#     for (scorer, score) in scores.items():
#         for (matching_piece, grade) in score.items():
#             table_rows.append([
#                 "%s %s (m %s)" % (snippet.piece, snippet.part, snippet.offset),
#                 ' '.join(snippet.simple_line()),
#                 scorer,
#                 matching_piece,
#                 grade
#             ])
# table_rows.sort(key=lambda x: (x[0], x[2], -1*x[4]))
# print(tabulate(table_rows, headers=table_headers))

# sqlsystem = SqlIRSystem('example.db.sqlite', index_methods, scorer_methods, piece_paths)

sqlsystem = SqlIRSystem('example.db.sqlite', index_methods, scorer_methods, piece_paths, False)

print_timing("Sampling ranges for demonstration")
sample_paths = random.sample(piece_paths, min(5, len(piece_paths)))
sample_pieces = (corpus.parse(piece) for piece in sample_paths)
sample_streams = []
sample_details = []
for piece in sample_pieces:
    parts = list(piece.recurse().parts)
    part = random.sample(parts, 1)[0]
    num_of_measures = len(part.measures(0, None))
    idx = random.randint(0, num_of_measures-5)
    sample_streams.append(part.measures(idx, idx+4).recurse().notesAndRests)
    sample_details.append((piece.metadata.title, part, idx))

scores = [sqlsystem.query(query) for query in sample_streams]
scores_with_details = zip(sample_details, scores)
print_timing("Printing results")
print("==========================================================================")
table_rows = []
table_headers = ['Query Source', 'Grading Method', 'Piece', 'Grade']
for (detail, (score_item, offsets)) in scores_with_details:
    for (scorer, score) in score_item.items():
        for (matching_piece, grade) in list(score.items())[:5]:
            table_rows.append([
                "%s %s (m %s)" % (detail[0], detail[1].partName, detail[2]),
                scorer,
                matching_piece,
                grade
            ])
table_rows.sort(key=lambda x: (x[0], x[1], -1*x[3]))
print(tabulate(table_rows, headers=table_headers))

input("\nDone - press enter to exit.")