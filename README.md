# Fuzzy Information Retrieval for Musical Scores (FIRMS)

FIRMS is an IR system designed for performing fuzzy searches against a corpus of musical scores. Users provide snippets of a musical work using a common digital music representation (e.g. MusicXML) and FIRMS compares it against a corpus of pre-indexed musical scores to efficiently rank and return results. The retrieval process is "fuzzy" because FIRMS is designed to be resilient against several common sources of transcription error, from simple typos, to aural rythmic ambiguity and key transposition.

## Setup

FIRMS can be set up manually by installing the following dependencies along with *Python 3+*:

* music21
* tabulate
* click
* scipy

To install locally with a given Python distribution:

`path/to/pip install music21 tabulate click scipy`

If using VirtualEnv:

`virtualenv firms`
`activate firms`
`pip install music21 tabulate click scipy`

Using the Anaconda python distribution:

`conda create -n firms python=3`
`activate firms`
`pip install music21 tabulate click scipy`

## Usage

FIRMS can be used as either a library (by importing modules from the `firms` namespace) or through a command line interface (CLI). The CLI is defined in `firms_cli.py` and can be run interactively to explore available commands and options:

> `path/to/python.exe firms_cli.py`

This will display a list of available commands. To see more detail about a particular command or group of commands, append `--help` to the command. For example, to see more detail about initializing a FIRMS index, run

> `python.exe firms_cli.py create --help`

At a broad level, the CLI offers the following features:

1. Create a FIRMS index
2. Add pieces to the index by specifying a composer, a path to a valid MusicXML file, or by adding all pieces in the music21 corpus
3. Show general information about the stored data
4. Query for a piece by providing an example via MusicXML or in tinynotation
5. Show a piece as MusicXML
5. Evaluate the system by randomly selecting sections from the music21 corpus and probabilistically introducing various types of errors

## Methods

## Architecture

At a fundamental level, FIRMS operates primarily on the concept of *stemming*. Each piece is broken into a number of small sections called *snippets*. These snippets are passed through several stemmers, each of which produces one or more *stems* capturing a particular dimension of the snippet, for example the pitches, rhythms, or contour of the snippet. These stems are persisted in an index for efficient lookup.

When a user enters a query, the query is passed through the same process, first breaking it up into snippets, then passing each snippet through the same stemmers. The resulting stems are looked up in the pre-constructed index, returning a list of locations within each piece that match the given snippet. From there, the results may be aggregated using one of several scoring mechanisms.

### Implementation

This particular implementation uses a local SQLite database to store the pre-computed snippets, stems, and other information.

### Scaling and Improvements

One interesting side-effect of the chosen architecture is that the applciation may be trivially scaled by hosting multiple instances behind a load balancer. On insert, an arbitrary instance could be chosen to store the piece. On query, a scatter-gather approach could pass the query to each instance, and the final results streamed back to the load balancer for aggregation. This approach would enable parallel persistent storage IO on each instance. With some further modification, each instance could be configured to locally aggregate results before passing them on for final aggregation, effectively recreating the MapReduce pipeline.

There are many musical aspects not captured by the current implementation, including:

* Unpitched percussion
* Tied notes
* Repeated sections

## Examples

The `./examples` directory contains a number of example music scores that can be added to the system for demo purposes. Each of these pieces is in the public domain and are available at [OpenMusicScore](http://openmusicscore.org/). To add these pieces to the index, run

> `python.exe firms_cli.py add dir "examples"`

Each piece can be queried using the CLI method:

> `python.exe firms_cli.py query tiny <tiny-query>`

Replace `<tiny-query>` in the command above with the query corresponding to the piece in the table below:

| Piece | Query |
| ----- | ----- |
| Amazing Grace | tinynotation: g8 c'2 e'8 c' e'2 d'4 c'2 a4 g2 g4 c'2 e'8 c' e'2 d'4 g'2  |
| Entertainer |  |
| March of the Wooden Soldiers |  |
| Ode to Joy |  |
| Korsakov Op 11 No 4 |  |

More information on tinynotation can be found [in the music21 documentation](http://web.mit.edu/music21/doc/moduleReference/moduleTinyNotation.html).