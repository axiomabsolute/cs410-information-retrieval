1. Intro
    * Firms is a fuzzy information retrieval system for music scores.
    * It allows users to lookup music scores by providing small exemplar snippets.
    * The system is designed to accommodate different potential sources of error, from simple transcription mistakes to notational and aural ambiguities.
2. Setup
    * Firms requires Python 3 to run.
    * I'll be using the Anaconda distribution of Python to create a clean, isolate Python 3.6 environment for this demonstration.
        - Other environment management tools should also work, such as virtualenv and pyenv
        - Firms is compatible with local Python installations as well, as long as it's 3.0+
    * `conda create -n firmsdemo -y python=3.6`
    * `activate firmsdemo`
        - On Unix-like systems, `source activate firmsdemo`
    * The last step is to use pip, the Python package manager, to install firms
        - `pip install firms`
    * This will install firms, its dependencies, and the CLI tool.
3. Introducing the CLI
    * Firms consists of both a library of components that can be used to build an IR system, as well as a CLI tool. The CLI tool acts as an example of such an IR system.
    * The CLI is installed automatically when Firms is installed through pip, and can be accessed with the `firms` command.
        - `firms`
    * The CLI features a hierarchy of commends. Simply entering `firms` without any arguments displays a short description of the system and a list of available commands. Appending `--help` to any command reveals more details about that command and any associated subcommands.
    * For example, to see more information about the `add` comamnd:
        - `firms add --help`
    * Broadly, Firms supports two actions: adding pieces to the system and querying pieces already in the system.
4. Adding Pieces
    * To start out, we'll add a small collection of 6 pieces from the example directory by running
        - `firms add dir examples`
    * This command recursively walks over files in the specified directory and tries to add them to a sqlite3 database stored in the current directory as `firms.sqlite.db`.
    * Notice that the output says "Skipping piece ode-to-joy.query.xml: only mxl and xml files supported". Files that end in `.query.xml` are assumed to represent user queries, and are ignored by the `add dir` command.
    * During the ingest process, Firms breaks each piece up into many small, overlapping *snippets* of notes. These snippets are passed through a set of *stemmers* to produce one or more *stems*.  Each stem captures a subset of the musical features from the orignal snippet while ignoring other features. Combined together, the stems for a single snippet collectively represent the original snippet, and all stems for a piece collecetively represent the piece.
5. Basic Information
    * The stems produced by the `add` command, along with the lineage information about where the stems came from and what method generated them, are stored in a sqlite3 database file. To verify that this worked, run the following command to gather some basic counts about the data currently in the system:
        - `firms info general`
    * This command shows various counts for data within the system. The first value is `stemmers`.  The system implemented by the Firms CLI includes 6 different stemmers: absolute pitch, pitch without octave, interval, pitch contour, rhythm, normalized rhythm.  More information about the different stemming methods can be found in the help documentation for the `firms.stemmers` module.
    * The `pieces` value shows the number of pieces currently indexed. We just added 6 pieces, which matches what's shown. The `parts` value represents the number of distinct parts defined by the different pieces. Two of the pieces have two parts, and the remaining have one part each, leading to 8 total parts.
    * The `snippets` value shows the number of individual units the pieces were divided into. The 6 pieces in the example directory are broken up into over 1,000 overlapping snippets! The system represents these internally as offsets within the originating piece and part. The `stems` value represents the total number of individual stems produced by the stemmers. Note that although there are 6 stemmers and over 1,000 stemmers, there are well under the expecterd number of stems (6*1,000=6,000). Each stem value stores its texutal representation. For efficiency, snippets which produce the same stem use a reference to a normalized stem value. That is to say, if two snippets generate the same textual stem reprsentation (e.g. 'rest rest rest rest rest' for a sequence of five rests) then there will only be one entry in the stems table.
    * The normalized references are tracked in the final value, `entries`. We expect this value to have a lower bound of (snippets * stemmers). In practice, snippets often produce more than one stem per stemmer, with each stem representing a separate musical *voice* within the snippet. This tiny sample of 6 musical scores results in almost 12,000 individual entries within the index.
6. Querying
7. Evaluation
8. Cleanup
    * To clean up the environment at the end of this tutorial, run:
    * `activate root`
    * `conda remove --name firmsdemo --all`