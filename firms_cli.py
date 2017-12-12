"""Fuzzy Information Retrieval for Music Scores"""

from operator import attrgetter
import random
from itertools import groupby
from scipy import stats
import csv
from abc import ABCMeta, abstractmethod

from music21 import converter, corpus, note, stream
from music21 import stream as m21stream
from tabulate import tabulate
import click

from firms.sql_irsystems import SqlIRSystem
from firms.graders import Bm25Grader, LogWeightedSumGrader
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

weights2 = {'By Pitch': 4.3, 'By Simple Pitch': 2.5, 'By Interval': 3.0, 'By Contour': -1.94, 'By Rythm': 1.36, 'By Normal Rythm': -2.85}
grader_methods = {
    'BM25': Bm25Grader(),
    'LogWeightedSumGrader': LogWeightedSumGrader(weights2)
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

operations = ['replace', 'remove', 'augment']
note_names = list('efgabcde')
accidentals = ['', '#', '-']
octaves = list(range(-1, 14))
durations = ['whole', 'half', 'quarter', '16th', '32nd']

class TranscriptionErrorType():
    def __init__(self, erate, efunction, name):
        self.error_rate = erate
        self.efunction = efunction
        self.name = name

    def introduce_error(self, sample_stream):
        return self.efunction(sample_stream)

def new_random_note_or_rest():
    new_note = None
    new_duration = random.choice(durations)
    if random.random() < .5:
        new_pitch = random.choice(note_names)
        new_accidental = random.choice(accidentals)
        new_octave = random.choice(octaves)
        new_note = note.Note(new_pitch, new_accidental, new_octave, type=new_duration)
    else:
        new_note = note.Rest(type=new_duration)
    return new_note

def add_note_error(sample_stream):
    result = stream.Stream(sample_stream)
    random_note_idx = random.randint(0, len(result.notesAndRests))
    print("\tIntroducing error: Note add")
    new_note = new_random_note_or_rest()
    result.insert(random_note_idx, new_note)
    return result

def remove_note_error(sample_stream):
    result = stream.Stream(sample_stream)
    random_note_idx = random.randint(0, len(result.notesAndRests))
    print("\tIntroducing error: Note remove")
    random_note = result.getElementAtOrBefore(random_note_idx, [note.Rest, note.Note])
    result.remove(random_note, firstMatchOnly=True, shiftOffsets=True)
    return result

def replace_note_error(sample_stream):
    result = stream.Stream(sample_stream)
    random_note_idx = random.randint(0, len(result.notesAndRests))
    print("\tIntroducing error: Note replace")
    random_note = result.getElementAtOrBefore(random_note_idx, [note.Rest, note.Note])
    result.replace(random_note, new_random_note_or_rest())
    return result

def transposition_error(sample_stream):
    print("Introducing error: transposition")
    return sample_stream.transpose(random.randint(-5,5))

def build_error_types(add_note_error_rate, remove_note_error_rate, replace_note_error_rate, transposition_error_rate):
    return [
        TranscriptionErrorType(add_note_error_rate, add_note_error, 'Add Note Error'),
        TranscriptionErrorType(remove_note_error_rate, remove_note_error, 'Remove Note Error'),
        TranscriptionErrorType(replace_note_error_rate, replace_note_error, 'Replace Note Error'),
        TranscriptionErrorType(transposition_error_rate, transposition_error, 'Transposition Error')
    ]

def introduce_error(sample_stream, erate, transcription_error_types):
    # Sample erate. If false, return
    if random.random() > erate:
        return sample_stream
    # Combine error types into a single distribution, sample to select an error type
    cumulative_error_type = 0
    error_type_sample = random.random()
    for tet in transcription_error_types:
        cumulative_error_type = cumulative_error_type + tet.error_rate
        if error_type_sample <= cumulative_error_type:
            print("Introducing error type %s" % tet.name)
            return tet.introduce_error(sample_stream) 
    print("No error added")
    return sample_stream

@click.command()
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def create(path):
    """Create or overwrite a existing FIRMs index"""
    SqlIRSystem(path, index_methods, grader_methods, [], True)

def connect(path):
    return SqlIRSystem(path, index_methods, grader_methods, [], False)

@click.group()
def add():
    """
    Group of commands for adding pieces to the FIRMS index
    """
    pass

@click.command("piece")
@click.option('--piecepath', help="Path to MusicXML file")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def add_piece(piecepath, path):
    """Add musicXML piece to firms index"""
    sqlIrSystem = connect(path)
    stream = converter.parse(piecepath)
    for piece in stream.recurse(classFilter=m21stream.Score, skipSelf=False):
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
        stream = corpus.parse(path)
        for piece in stream.recurse(classFilter=m21stream.Score, skipSelf=False):
            sqlIRSystem.add_piece(piece, path)

@click.command('music21')
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def add_music21(path):
    """
    Add all pieces supplied in the default music21 corpus
    """
    sqlIRSystem = connect(path)
    paths = corpus.getPaths()
    num_pieces = len(paths)
    for idx,path in enumerate(paths):
        print("Adding piece %s of %s" % (idx, num_pieces))
        try:
            stream = corpus.parse(path)
            for piece in stream.recurse(classFilter=m21stream.Score, skipSelf=False):
                sqlIRSystem.add_piece(piece, path)
        except:
            print("\tUnable to process piece %s" % path)

@click.command("tiny")
@click.option('--query', help="Snippet of target piece, in TinyNotation")
@click.option('--output', default=None, help="Path to write results out to")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def query_tiny(query, output, path):
    """
        Query for piece using tiny notation

        Examples firms_cli.py tiny --query "tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c" --path "example.db.sqlite" 
    """
    sqlIrSystem = connect(path)
    stream = converter.parse(query)
    notes = stream.recurse().notesAndRests
    results = sqlIrSystem.query(notes)
    formatted_results = print_results(results)
    if output:
        with open(output, 'w') as outf:
            writer = csv.writer(outf, lineterminator="\n")
            for row in formatted_results:
                writer.writerow(row)

@click.command("piece")
@click.option('--file', help="Path to Music XML (or MXL) file containing query")
@click.option('--output', default=None, help="Path to write results out to")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def query_piece(file, output, path):
    sqlIrSystem = connect(path)
    stream = converter.parse(file)
    results = sqlIrSystem.query(stream)
    formatted_results = print_results(results)
    if output:
        with open(output, 'w') as outf:
            writer = csv.writer(outf, lineterminator="\n")
            for row in formatted_results:
                writer.writerow(row)

@click.group()
def query():
    """
    Query for a piece using tiny notation or by providing an exemplar Music XML file
    """
    pass

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
    print_pieces(list(result))

@click.command("piece")
@click.option("--id", help="ID of the piece to lookup")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def info_piece(id, path):
    sqlIrSystem = connect(path)
    results = sqlIrSystem.piece_by_id(id)
    print_pieces(results)

@click.command("evaluate")
@click.option('--n', default=2, help="Number of pieces to sample")
@click.option('--erate', default=0.0, help="Rate at which to simulate error")
@click.option('--minsize', default=3, help="Minimum sample size (in measures)")
@click.option('--maxsize', default=7, help="Maximum sample size (in measures)")
@click.option('--add_note_error', default=0.0, help="Error by adding a random note in the snippet with a random note value")
@click.option('--remove_note_error', default=0.0, help="Error by removing a random note")
@click.option('--replace_note_error', default=0.0, help="Error by replacing a random note in the snippet with a random note value")
@click.option('--transposition_error', default=0.0, help="Error by transposing the key of the snippet")
@click.option('--output', default=None, help="Path to write results out to")
@click.option('--noprint', default=False, help="Set to True to skip printing results")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def evaluate(n, erate, minsize, maxsize, add_note_error, remove_note_error, replace_note_error, transposition_error, output, noprint, path):
    """
    Select random samples from index and run IR evaluation.

    Select n random samples of length [minsize, maxsize] measures
    With probability erate, introduce errors to the sampled snippets
        Select error using relative weights of each  of the --*error parameters
    """
    print("Running evaluation with %s samples" % n)
    sqlIrSystem = connect(path)
    pieces = sqlIrSystem.pieces()
    print("Selecing sample pieces")
    sample_pieces = random.sample(pieces, n)
    details = []
    query_results = []
    for idx,sample_piece in enumerate(sample_pieces):
        try:
            sample_piece_name, sample_piece_path, sample_piece_id = sample_piece
            print("Sample %s: %s (%s)" % (idx + 1, sample_piece_name, sample_piece_path))
            piece = corpus.parse(sample_piece_path)
            part = random.choice(list(piece.recurse().parts))
            num_of_measures = len(part.measures(0,None))
            sample_size = random.randint(minsize, maxsize)
            idx = random.randint(0, num_of_measures-sample_size)
            sample_stream = part.measures(idx, idx+sample_size).recurse().notesAndRests
            sample_detail = (sample_piece_name, part, idx, sample_piece_path, sample_piece_id)
            sample_stream = introduce_error(sample_stream, erate, build_error_types(add_note_error, remove_note_error, replace_note_error, transposition_error))
            print("\tQuerying..")
            query_result = sqlIrSystem.query(sample_stream)
            query_results.append(query_result)
            details.append(sample_detail)
        except Exception as e:
            print("Unable to process piece %s" % sample_piece_path)
            print(e)
    evaluations = print_evaluations(details, query_results, noprint)
    print("Computing evaluation metrics")
    # Filter by [3] (is actual)
    tp_evaluations = [x for x in evaluations if x[3]]
    # Aggregate by [1] (grading method)
    tps_by_method = dict((k, list(g)) for k,g in groupby(sorted(tp_evaluations, key=lambda x: x[1]), lambda x: x[1]))
    # Compute statistics on [5] (rank) and [6] (grade)
    aggregate_rank_results = {method: stats.describe([tp[4] for tp in tps]) for method,tps in tps_by_method.items()}
    for method, description in aggregate_rank_results.items():
        print("Statistics for %s" % method)
        for stat,val in zip(description._fields, description):
            print("\t%s: %s" % (stat,val))
    if output:
        with open(output, 'w') as outf:
            writer = csv.writer(outf, lineterminator="\n")
            for row in evaluations:
                writer.writerow(row)

@click.command("show")
@click.option("--piece_path", help="Partial path to a piece to show")
@click.option('--path', default=DEFAULT_DB_PATH, help="Path to sqlite DB file; defaults to `./firms.sqlite.db`")
def show(piece_path, path):
    """
    Retrieve a piece and open it as a MusicXML file.

    Warning: for some file types this may open up several browser tabs, which can be slow.
    """
    try:
        sqlIrSystem = connect(path)
        full_path = [p for (n, p) in sqlIrSystem.pieces() if piece_path.lower() in p.lower()][0]
        piece = corpus.parse(full_path)
        piece.show()
    except Exception as e:
        print("Unable to show %s" % piece_path)
        print(e)

def print_results(grader_results):
    table_rows = []
    table_headers = ['Grading Method', 'Piece', 'Rank', 'Grade']
    for grader,results in grader_results.items():
        results_ordered_by_grade = sorted(results, key=attrgetter('grade'), reverse=True)
        for result_number,(piece, grade, meta) in enumerate(results_ordered_by_grade):
            if result_number < 10:
                table_rows.append([
                    grader,
                    piece,
                    result_number,
                    grade
                ])
    print(tabulate(table_rows, headers=table_headers))
    return table_rows

def print_evaluations(sample_details, query_results, skip_print):
    table_rows = []
    table_headers = ['Query Source', 'Grader', 'Piece ID', 'Actual', 'Rank', 'Grade']
    for (detail, grader_results) in zip(sample_details, query_results):
        for grader,results in grader_results.items():
            results_ordered_by_grade = sorted(results, key=attrgetter('grade'), reverse=True)
            for result_number,(piece, grade, meta) in enumerate(results_ordered_by_grade):
                is_actual = detail[4] == piece
                if result_number < 5 or is_actual:
                    piece_split = detail[0].split('site-packages')
                    truncated_piece = '..%s' % piece_split[-1] if len(piece_split) > 1 else piece
                    table_rows.append([
                        "%s %s (m %s)" % (detail[0], detail[1].partName, detail[2]),
                        grader,
                        truncated_piece,
                        is_actual,
                        result_number,
                        round(grade, 2)
                    ])
    table_rows.sort(key=lambda x: (x[0], x[1], -1*x[5]))
    if not skip_print:
        print(tabulate(table_rows, headers=table_headers))
    return table_rows

def print_pieces(pieces):
    table_headers = ['Name', 'Path', 'ID']
    print(tabulate(pieces, headers=table_headers))

@click.group()
def cli():
    pass

# Build command groups
info.add_command(info_pieces)
info.add_command(info_general)
info.add_command(info_piece)

add.add_command(add_piece)
add.add_command(add_composer)
add.add_command(add_music21)

query.add_command(query_tiny)
query.add_command(query_piece)

# Add groups to root
cli.add_command(info)
cli.add_command(add)
cli.add_command(query)

# Add orphan commands
cli.add_command(create)
cli.add_command(show_composers)
cli.add_command(evaluate)
cli.add_command(show)

if __name__ == "__main__":
    cli()