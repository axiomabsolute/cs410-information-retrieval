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
4. Adding Pieces
5. Querying
6. Evaluation
7. Cleanup
    * To clean up the environment at the end of this tutorial, run:
    * `activate root`
    * `conda remove --name firmsdemo --all`