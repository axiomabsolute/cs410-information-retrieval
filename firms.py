from operator import attrgetter

from music21 import converter, corpus
from tabulate import tabulate

from firms.sql_irsystems import SqlIRSystem
from firms.graders import count_grader, log_count_grader, weighted_sum_grader_factory, log_weighted_sum_grader_factory, stem_counter_by_piece, log_weighted_sum_grader_weightless_factory, bm25_factory
from firms.stemmers import index_key_by_pitch, index_key_by_simple_pitch, index_key_by_interval, index_key_by_contour, index_key_by_rythm, index_key_by_normalized_rythm

"""
A command line CLI for interacting with a FIRMs system.

API:

create [path=./firms.sqlite.db] - creates a SQLite FIRMs database at given path
connect [path=./firms.sqlite.db] - connects to a SQLite FIRMs database at given path
add stemmer [path] - adds the specified stemmer by attempting to re-fetch each piece and process with stemmer
add piece [path] - adds the specified piece to the index
    path may be a file path or composer name. File path must contain a \ or / character
list [attribute] - list various attributes about indexed data
    composers - piece information by composer
    pieces - piece information
    paths - paths originally used to build index
    parts - parts information
    stemmers - stemmers used
    info - general info
check [attribute] [value] - checks whether the given piece is in the index
    name - the name of the piece
    path - the original path to the piece
    file - the filename for the piece
query [tiny|path] - reads tiny notation or musicXML file at the given path and queries the database
similar [path] - reads piece located at path and uses it as input to a query
"""

sqlsystem = None

index_methods = {
    'By Pitch': index_key_by_pitch,
    'By Simple Pitch': index_key_by_simple_pitch,
    'By Contour': index_key_by_contour,
    'By Interval': index_key_by_interval,
    'By Rythm': index_key_by_rythm,
    'By Normal Rythm': index_key_by_normalized_rythm
}

weights = {'By Pitch': 2, 'By Simple Pitch': 1, 'By Interval': .2, 'By Contour': .1, 'By Rythm': .1, 'By Normal Rythm': .1}
weights2 = {'By Pitch': 4.3, 'By Simple Pitch': 2.5, 'By Interval': 3.0, 'By Contour': -1.94, 'By Rythm': 1.36, 'By Normal Rythm': -2.85}
weights3 = dict(zip(index_methods.keys(), [ 4.38148063, 4.38148063, 2.12716021, 0.46437347, 0.46437347, 0.46437347]))
scorer_methods = {
    # 'LogLinar': log_weighted_sum_grader_factory(weights),
    # 'LogLinear2': log_weighted_sum_grader_factory(weights2),
    # 'LogLinear3': log_weighted_sum_grader_factory(weights3),
    'BM25': bm25_factory()
}

DEFAULT_DB_PATH = "firms.sqlite.db"

def create(path=DEFAULT_DB_PATH):
    SqlIRSystem(path, index_methods, scorer_methods, [], True)

def connect(path):
    return SqlIRSystem(path, index_methods, scorer_methods, [], False)

def add_piece(piece_path, db_path=DEFAULT_DB_PATH):
    sqlIrSystem = connect(db_path)
    piece = corpus.parse(piece_path)
    sqlIrSystem.add_piece(piece, piece_path)

def query_tiny(tinyquery, db_path=DEFAULT_DB_PATH):
    sqlIrSystem = connect(db_path)
    stream = converter.parse(tinyquery)
    notes = stream.recurse().notesAndRests
    results = sqlIrSystem.query(notes)
    return results

def print_results(grader_results):
    table_rows = []
    table_headers = ['Grading Method', 'Piece', 'Rank', 'Grade']
    for grader,results in grader_results.items():
        results_ordered_by_grade = sorted(results, key=attrgetter('grade'), reverse=True)
        for result_number,(piece, grade, meta) in enumerate(results_ordered_by_grade):
            if result_number < 5:
                table_rows.append([
                    grader,
                    piece,
                    result_number,
                    grade
                ])
    print(tabulate(table_rows, headers=table_headers))

if __name__ == "__main__":
    print_results(query_tiny("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c", "example.db.sqlite"))