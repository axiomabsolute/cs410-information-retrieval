"""Fuzzy Information Retrieval for Music

Usage:
  firms_cli.py create [dbpath]
  firms_cli.py add <path> [dbpath]
  firms_cli.py query <tinyquery> [dbpath]
  naval_fate.py (-h | --help)
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --dbpath      Path to FIRMs SQLite db
"""

from operator import attrgetter

from music21 import converter, corpus
from tabulate import tabulate

from firms.sql_irsystems import SqlIRSystem
from firms.graders import bm25_factory
from firms.stemmers import index_key_by_pitch, index_key_by_simple_pitch, index_key_by_interval,\
    index_key_by_contour, index_key_by_rythm, index_key_by_normalized_rythm

index_methods = {
    'By Pitch': index_key_by_pitch,
    'By Simple Pitch': index_key_by_simple_pitch,
    'By Contour': index_key_by_contour,
    'By Interval': index_key_by_interval,
    'By Rythm': index_key_by_rythm,
    'By Normal Rythm': index_key_by_normalized_rythm
}

scorer_methods = {
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

def dispatch(method, args):
    if method == 'create':
        pass
    elif method == 'add':
        pass
    elif method == 'query':
        pass
    else:
        print("Unknown command `%s`" % method)

if __name__ == "__main__":
    # print_results(query_tiny("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c", "example.db.sqlite"))