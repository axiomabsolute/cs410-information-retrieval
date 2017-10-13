Project Description
===================

This project explores how concepts in textual information retrieval can be applied to efficiently index and search for musical scores. I intend to focus on two particular use-cases:

1. A listener searching for a specific piece by trying to reproduce a small section by ear.
2. A composer interested in surveying pieces which feature similar themes.

In the first case, listeners are generally not able to exactly reproduce music by ear (e.g. to exactly match tempo, identify pitches, or reproduce rythms). Furthermore, there is often some ambiguity in notation (e.g. a quarter and half note sound like they are the same length if the tempo is two times as fast for the half note).

In the second case, the goal is explicitly *not* to find exact matches, but rather to find variations of the provided theme. Variation can occur rhythmically (stretching, compressing, or changing rythm while maintaining pitches), tonally (by shifting pitch, changing keys, inversions, etc), or more broadly may simply follow the same contour or chord progression.

Several tools offer functionality which partially overlaps with this proposal, including [hymnary.org](https://hymnary.org/melody/search), [bestclassicaltunes.com](http://bestclassicaltunes.com/DictionaryPiano.aspx), [kooplet.com](http://www.kooplet.com/cgi-bin/kooplet/search.pl), and [themefinder.org](http://www.themefinder.org/). All of these tools allow users to enter notes in some format (some preserving rythm, others only pitch) through a web interface to search through a database of musical scores. Of the tools listed, only Themefinder provides additional search options for concepts such as interval and contour.

These tools all operate against a fixed set of songs and provide little feedback to the user about how and why different results match a given query. Overall, these tools appear to focus on the first use-case described above, but do not enable compositional exploration or analytical tasks. The goal of this project is an open source system which users can run locally, augment with personal compositions, and easily extend with additional indexing methods.

Two existing tools for computational musicology will be used to read, process, and analyze musical scores. The first tool, `music21`, is a Python library developed by MIT's computational musicology group.  The second, `Humdrum`, is a set of Unix utilities and extensions developed by Ohio State's Cognitive Systematic Musicology Lab.

The proposed system will rely heavily on segmentation and stemming methods to break each piece down into small snippets of music and produce several stemmed versions of each snippet, designed to capture various dimensions of the snippet (such as pitch, interval, contour, etc).  These stemmed snippets will be used to generate a reverse index for each stemming method. Given a query, the system will repeat the process to break the query down into snippets and stem those snippets using the same methods used to index the corpus of musical scores. The stemmed query snippets will then be used to retrieve corpus snippets from the reverse indexes, along with the parent pieces each snippet is derived from. Snippets will be aggeregated by piece and method, allowing for the system to compute a weighted aggregate score for each piece, to be used to rank final results.

The end product will be a command line tool for a complete IR system, allowing users to add items to the index, review the indexed corpus, and submit queries in one or more supported textual formats. The system will respond with a ranked list of relevant musical scores, along with information on which parts of the score matched the query and along what dimensions.

Timeline:

* Weeks 4-6 : Develop initial prototype to parse scores and break up into snippets
* Weeks 6-8 : Enhance system to handle chords, multi-voice pieces, and index by absolute pitch
* Weeks 10-12 : Develop additional stemming methods, explore score aggregation methods, and persisting indexes to disk
* Till end of term : Polish user experience
