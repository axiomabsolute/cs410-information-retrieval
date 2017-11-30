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
import click

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

@click.command()
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file")
def create(path):
    """Create or overwrite a existing FIRMs index"""
    SqlIRSystem(path, index_methods, scorer_methods, [], True)

def connect(path):
    return SqlIRSystem(path, index_methods, scorer_methods, [], False)

@click.command("add")
@click.option('--piece', help="Path to MusicXML file")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file")
def add_piece(piece_path, db_path=DEFAULT_DB_PATH):
    """Add musicXML piece to firms index"""
    sqlIrSystem = connect(db_path)
    piece = corpus.parse(piece_path)
    sqlIrSystem.add_piece(piece, piece_path)

@click.command("tiny")
@click.option('--query', help="Snippet of target piece, in TinyNotation")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file")
def query_tiny(query, path=DEFAULT_DB_PATH):
    """
        Query for piece using tiny notation

        Examples firms_cli.py tiny --query "tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c" --path "example.db.sqlite" 
    """
    sqlIrSystem = connect(path)
    stream = converter.parse(query)
    notes = stream.recurse().notesAndRests
    results = sqlIrSystem.query(notes)
    return print_results(results)

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

@click.group()
def cli():
    pass

cli.add_command(create)
cli.add_command(add_piece)
cli.add_command(query_tiny)

if __name__ == "__main__":
    cli()