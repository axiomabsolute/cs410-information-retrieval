# Fuzzy Information Retrieval for Musical Scores (Firms)

Firms is an IR system designed for performing fuzzy searches against a corpus of musical scores. Users provide snippets of a musical work using a common digital music representation (e.g. MusicXML) and Firms compares it against a corpus of pre-indexed musical scores to efficiently rank and return results. The retrieval process is "fuzzy" because Firms is designed to be resilient against several common sources of transcription error, from simple typos, to aural rythmic ambiguity and key transposition.

## Setup

Firms is hosted on the Python Package Index (Pypi) and can be installed along with all required dependencies with the `pip` command:

> `pip install firms`

## Usage

Firms can be used as either a library (by importing modules from the `firms` namespace) or through a command line interface (CLI). The CLI is defined in `firms_cli.py` and can be run interactively to explore available commands and options:

> `firms`

This will display a list of available commands. To see more detail about a particular command or group of commands, append `--help` to the command. For example, to see more detail about initializing a Firms index, run

> `firms create --help`

or for different options for adding pieces to the index:

> `firms add --help`

Many commands have subcommands supporting related operations. For instance, to add all MusicXML pieces from a directory, use the `add dir` subcommand:

> `firms add dir /path/to/directory`

At a broad level, the CLI offers the following features:

1. Create a Firms index
2. Add pieces to the index by specifying a composer, a path to a valid MusicXML file, or by adding all pieces in the music21 corpus
3. Show general information about the stored data
4. Query for a piece by providing an example via MusicXML or in tinynotation
5. Show a piece as MusicXML
6. Output the midi version of a piece
7. Evaluate the system by randomly selecting sections from the music21 corpus and probabilistically introducing various types of errors

## Examples

The `./examples` directory contains a number of example music scores that can be added to the system for demo purposes. Each of these pieces is in the public domain and are available at [OpenMusicScore](http://openmusicscore.org/). To add these pieces to the index, run

> `firms add dir "examples"`

Each piece can be queried using the CLI method:

> `firms query tiny <tiny-query>`

Replace `<tiny-query>` in the command above with the query corresponding to the piece in the table below. This query format is a simple ASCII-based notation for representing small snippets of music using standard western notation.

> More information on tinynotation can be found [in the music21 documentation](http://web.mit.edu/music21/doc/moduleReference/moduleTinyNotation.html).

| Piece | Query |
| ----- | ----- |
| Amazing Grace | tinynotation: g8 c'2 e'8 c' e'2 d'4 c'2 a4 g2 g4 c'2 e'8 c' e'2 d'4 g'2.~ g'2 e'4 g'4.~ e'8 g' e' c'2 g4 a4. c'8 c' a |
| Entertainer | tinynotation: d''16 e'' c'' a' a' b' g'8 d'16 e' c' a a b g8 d16 e c A A B A A- G8 |
| March of the Wooden Soldiers | tinynotation: d'8 r d' r b8. a#16 b8 r16 c'#16 d'8 r d' r b8. a#16 b8 r16 c'#16 |
| Ode to Joy | tinynotation: b b c' d' d' c' b a g g a b b4. a8 a2 |
| Deck the Halls | tinynotation: d'4. c'8 b4 a g a b g a8 b c' a b4. a8 g4 f# g2 |

For example, to run the query for *Entertainer* from the table above, run:

> `firms query tiny "tinynotation: d''16 e'' c'' a' a' b' g'8 d'16 e' c' a a b g8 d16 e c A A B A A- G8"`

In addition, an XML sample of "Ode to Joy" is provided in the `examples` directory, and can be used like so:

> `firms query xml examples/ode-to-joy.query.xml`

### Examples with Errors

The table below contains versions of the sample queries above with a different type of musical error included.

| Piece | Query | Error Type |
| ----- | ----- | ---------- |
| Amazing Grace | tinynotation: g8 c'2 e'8 c' e'2 d'4 c'2 a4 g2 g4 g4 c'2 e'8 c' e'2 d'4 g'2. g'2 | Extra Note |
| Entertainer | tinynotation: d''16 e'' c'' a' a' b' g' d' e' c' a a b g8 d16 e c A A B A A- G8" | Wrong Note |
| March of the Wooden Soldiers | tinynotation: d'8 r d' b8. a#16 b8 r16 c'#16 d'8 r d' r b8. a#16 b8 r16 c'#16 | Missing Note |
| Ode to Joy | tinynotation: d' d' e'- f' f' e'- d' c' b- b- c' d' d'4. c'8 c'2 | Transposed |
| Deck the Halls | tinynotation: d'2. c'4 b2 a g a b g a4 b c' a b2. a4 g2 f# g1 | Stretched Rhythm |

FIRMs is designed to be accomodate some level of error in the user input.

### Repeated sections

Failing to trace through repeated sections of music causes issues for songs with a heavily repetative structure. The performance of Firms is highly dependent on how these types of songs are notated. Explicitly writing out repeated sections in a flat format greatly improves the performance. This can be seen in the *Amazing Grace* query in the "Examples" section above. This example contains the main theme of the song, but the BM25 method fails to score it highly because the repeated sections are ignored from the original score. The "Amazing Grace with Drums Explicit Repeat" example is an alternate engraving of the "Amazing Grace with Drums" score with repeated sections written out linearly, as they would be heard by an audience. This example scores *higher* than the original version because the repeats are effectively captured.

Firms can automatically expand repeated sections during the indexing process. The various `add` commands take a boolean flag to enable the conversion:

> `firms add dir ./examples --explicit_repeats True`

Note that this process can slow down ingest time significantly. If a piece does not contain any repeated sections, or the repeated sections are malformed in some way, the following error message will be shown, and the ingestion process will continue with the original unexpanded version:

> Unable to expand piece. Continuing with original

## Evaluation

In addition to the examples shown above, the FIRMs CLI includes a command for performing random probabilistic evaluation by sampling the pieces included in the index.

To run an evaluation, first add some pieces to the corpus. Note, this command may take some time (~5 minutes on my laptop) as it adds over 400 pieces to the index.

> `firms add composer bach --filetype xml`

Then run an evaluation, specifying the number of samples to take. Note, this may take some time to complete (~15 minutes for my laptop). Try `--n 10` for a faster result (~1.5 min).

> `firms exaluate --n 100 --noprint True`

This will take 100 samples of various lengths from the pieces available in the FIRMs index, perform a search based on the sample, and collect statistics on the average rank of the correct result. The `--noprint True` option skips printing the individual query results tables, while still printing the aggregate true-positive ranking statistic. For exmaple, the results on my run were as follows:

'''
Statistics for BM25
        nobs: 100
        minmax: (0, 7)
        mean: 0.19
        variance: 0.882727272727
        skewness: 6.297878668097064
        kurtosis: 40.1179051948864
Statistics for LogWeightedSumGrader
        nobs: 100
        minmax: (0, 26)
        mean: 0.42
        variance: 6.85212121212
        skewness: 9.47574350344239
        kurtosis: 90.04614836416702
'''

This shows statistics on the ranks of true-positive results, broken down by the grading methods used. The field `nobs` represents the total number of observations. The `minmax` field shows the minimum and maximum ranks for true-positive results. The `mean`, `variance`, `skewness`, and `kurtosis` fields are statistics calculated based on the the ranks.

While this is interesting, it is not overly representative of realistic queries. First, these snippets are randomly selected, whereas users are more likely to enter memorable melodic lines and themes. Second, users are likely to include errors in their entries, either due to transcription or due to ambiguities in how a particular piece is notated.

Tackling the first issue is beyond the scope of this project, but the `evaluate` method includes a number of parameters for probabilistically introducing errors into the sample queries.

> `firms evaluate --n 100 --erate .2`

The `--erate .2` parameter gives each snippet a 20% chance of including an error. The type of error chosen is controlled by the parameters `--transposition_error`, `--replace_note_error`, `--remove_note_error`, and `--add_note_error`. These are decimal values between [0, 1) and should add up to 1, thus representing a probability distribution. By default, they are each set to `.25` to present an equal probability.

Often we're more concerned with whether the true-positive result is within the top K results returned, such as the first page of a search engine. To quantify this, we can configure the evaluation scorer to treat all results below K as a 0, while maintaining the rank of results beyond that.

> `firms evaluate --n 100 --topk 10`

This allows the system to be a little more flexible defining what it considers to be a correct result.

## Architecture

At a fundamental level, Firms operates primarily on the concept of *stemming*. Each piece is broken into a number of small sections called *snippets*. These snippets are passed through several stemmers, each of which produces one or more *stems* capturing a particular dimension of the snippet. For example, a stem may capture the pitches, rhythms, or contour of notes within snippet. These stems are persisted in an index for efficient lookup.

When a user enters a query, the query is passed through the same process, first breaking it up into snippets, then passing each snippet through the same stemmers. The resulting stems are looked up in the pre-constructed index, returning a list of locations within each piece that match the given snippet. From there, the results may be aggregated using one of several scoring mechanisms.

The implementation provides two built-in scoring mechanisms. The first is a log weighted sum of counts. The matching stems for each stemmer type are aggregated by taking the natural logarithm of the count, then multiplied by a per-stemmer weight value, and finally summed together to form the final grade. The second is a standard Okapi BM25 implementation without document length normalization. Two potential measures of document length which may improve the accuracy of this method are the total number of measures for a piece or the total number of snippets in a piece. A measure based approach ignores the density of notes within a measure: a measure with a single whole note would be weighted the same as a measure with a melodic line of sixteenth notes. The snippet count approach would disproportionally impact pieces with many parts or voices, as each part and voice acts as a multiplier for the number of snippets contained in a piece. For these reasons, document length normalization was not inlcuded for this project.

This particular implementation uses a local SQLite database to store the pre-computed snippets, stems, and other information as a flat-file relational structure. Each stemmer type is an instance of the abstract `FirmIndex` class, which hides the details of the storage mechanism used. This allows the underlying SQLite implementation to be swapped out for a more efficient storage mechanism without impacting the rest of the system.

### Scaling and Improvements

One interesting side-effect of the chosen architecture is that the applciation may be trivially scaled by hosting multiple instances behind a load balancer. On insert, an arbitrary instance could be chosen to store the piece. On query, a scatter-gather approach could pass the query to each instance, and the final results streamed back to the load balancer for aggregation. This approach would enable parallel persistent storage IO on each instance. With some further modification, each instance could be configured to locally aggregate results before passing them on for final aggregation.

There are many musical aspects not captured by the current implementation, including:

* Unpitched notes, e.g. percussion
* Tied notes
* Non-traditional western music notation

## Development

Configure .pypirc file with:

```
[distutils]
index-servers =
  pypi
  pypitest

[pypi]
username=user-name
password=user-password

[pypitest]
username=user-name
password=user-password
```

Then to create a new version:

1. `git commit`
2. Update setup.py `version` and `download_url`
3. `git tag <version-number>` and `git push --tags`
4. `python setup.py sdist upload -r pypitest`
5. `pip install --upgrade firms --no-cache-dir`