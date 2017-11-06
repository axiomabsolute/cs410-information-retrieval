"""
A command line CLI for interacting with a FIRMs system.

API:

connect [path] - connects to a SQLite FIRMs database at given path
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
query [tiny] - reads tiny notation and queries
similar [path] - reads piece located at path and uses it as input to a query
"""