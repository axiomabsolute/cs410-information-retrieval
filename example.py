import random
from operator import attrgetter
from tabulate import tabulate
from music21 import corpus
from firms.graders import count_grader, log_count_grader, weighted_sum_grader_factory, log_weighted_sum_grader_factory
from firms.stemmers import index_key_by_pitch, index_key_by_simple_pitch, index_key_by_rythm, index_key_by_normalized_rythm
from firms.models import MemoryIRSystem, print_timing
from firms.sql_irsystems import SqlIRSystem

print()
print_timing("Loading pieces")
piece_paths = corpus.getComposer('bach')

index_methods = {
    'By Pitch': index_key_by_pitch,
    'By Simple Pitch': index_key_by_simple_pitch,
    'By Rythm': index_key_by_rythm,
    'By Normal Rythm': index_key_by_normalized_rythm
}

weights = {'By Pitch': 2, 'By Simple Pitch': 1, 'By Rythm': .1, 'By Normal Rythm': .1}
scorer_methods = {
    'Count': count_grader,
    'Log Count': log_count_grader,
    'Linear': weighted_sum_grader_factory(weights),
    'LogLinar': log_weighted_sum_grader_factory(weights)
}

print_timing("Building IR system")
# irsystem = MemoryIRSystem(index_methods, scorer_methods, piece_paths)

sqlsystem = SqlIRSystem('example.db.sqlite', index_methods, scorer_methods, piece_paths, False)

print_timing("Sampling ranges for demonstration")
sample_paths = random.sample(piece_paths, min(10, len(piece_paths)))
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

print_timing("Scoring samples")
scores = []
for detail,query in zip(sample_details, sample_streams):
    print_timing("Querying %s (%s)" % (detail[0], detail[1].partName), 1)
    scores.append(sqlsystem.query(query))
scores_with_details = zip(sample_details, scores)
print_timing("Printing results")
print("==========================================================================")
table_rows = []
table_headers = ['Query Source', 'Grading Method', 'Piece', 'Is Actual', 'Rank', 'Grade']
for (detail, grader_results) in scores_with_details:
    for grader,results in grader_results.items():
        results_ordered_by_grade = sorted(results, key=attrgetter('grade'), reverse=True)
        for result_number,(piece, grade, meta) in enumerate(results_ordered_by_grade):
            is_actual = detail[0] == piece
            if result_number < 5 or is_actual:
                table_rows.append([
                    "%s %s (m %s)" % (detail[0], detail[1].partName, detail[2]),
                    grader,
                    piece,
                    is_actual,
                    result_number,
                    grade
                ])
table_rows.sort(key=lambda x: (x[0], x[1], -1*x[5]))
print(tabulate(table_rows, headers=table_headers))

input("\nDone - press enter to exit.")