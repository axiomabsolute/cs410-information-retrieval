"""Fuzzy Information Retrieval for Music Scores"""

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

composers_list = [
    "airdsAirs",
    "bach",
    "beethoven",
    "chopin",
    "ciconia",
    "corelli",
    "cpebach",
    "demos",
    "essenFolksong",
    "handel",
    "haydn",
    "josquin",
    "leadSheet",
    "luca",
    "miscFolk",
    "monteverdi",
    "mozart",
    "oneills1850",
    "palestrina",
    "ryansMammoth",
    "schoenberg",
    "schumann",
    "schumann_clara",
    "theoryExercises",
    "trecento",
    "verdi",
    "weber"
]

DEFAULT_DB_PATH = "firms.sqlite.db"

@click.command()
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def create(path):
    """Create or overwrite a existing FIRMs index"""
    SqlIRSystem(path, index_methods, scorer_methods, [], True)

def connect(path):
    return SqlIRSystem(path, index_methods, scorer_methods, [], False)

@click.group()
def add():
    pass

@click.command("piece")
@click.option('--piecepath', help="Path to MusicXML file")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def add_piece(piecepath, path):
    """Add musicXML piece to firms index"""
    sqlIrSystem = connect(path)
    piece = corpus.parse(piecepath)
    sqlIrSystem.add_piece(piece, piecepath)

@click.command("composer")
@click.option('--composer', help="Composer's name to add")
@click.option('--filetype', help="Filters list of pieces by file type")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def add_composer(composer, filetype, path):
    """
        Add all pieces by composer to firms index.
        Use `firms_cli.py composers` to see a list of composers.
    """
    sqlIRSystem = connect(path)
    paths = corpus.getComposer(composer, filetype)
    if len(paths) == 0:
        print("Error: no pieces found matching composer %s" % composer)
    for path in paths:
        piece = corpus.parse(path)
        sqlIRSystem.add_piece(piece, path)

@click.command("tiny")
@click.option('--query', help="Snippet of target piece, in TinyNotation")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def query_tiny(query, path):
    """
        Query for piece using tiny notation

        Examples firms_cli.py tiny --query "tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c" --path "example.db.sqlite" 
    """
    sqlIrSystem = connect(path)
    stream = converter.parse(query)
    notes = stream.recurse().notesAndRests
    results = sqlIrSystem.query(notes)
    return print_results(results)

@click.command("composers")
def show_composers():
    """
        Show a list of composers currently available in the music21 corpus.
    """
    print("Composers:")
    for c in composers_list:
        print("\t%s" % c)


@click.group()
def info():
    """
    Show information on one or more attributes 
    """
    pass

@click.command("general")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def info_general(path):
    """Show general aggregate information"""
    sqlIrSystem = connect(path)
    result = sqlIrSystem.info()
    max_key_len = max([len(str(r)) for r in result.keys()])
    max_value_len = max([len(format(v, "0,d")) for v in result.values()])
    for k,v in result.items():
        print("%s: %s" % (k.rjust(max_key_len + 2), format(v, "%s,d" % (max_value_len + 2))))

@click.command("pieces")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
@click.option('--name', default="", help="Case-insensitive plain text filter to match against name")
@click.option('--fname', default="", help="Case-insensitive plain text filter to match against file path")
def info_pieces(path, name, fname):
    """List pieces and composers"""
    sqlIrSystem = connect(path)
    result = filter(
                lambda x: fname.lower() in x[1].lower(),
                filter(lambda x: name.lower() in x[0].lower(),
                    sqlIrSystem.pieces()))
    print(list(result))

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

info.add_command(info_pieces)
info.add_command(info_general)

add.add_command(add_piece)
add.add_command(add_composer)

cli.add_command(create)
cli.add_command(add_piece)
cli.add_command(query_tiny)
cli.add_command(show_composers)
cli.add_command(info)
cli.add_command(add)

if __name__ == "__main__":
    cli()