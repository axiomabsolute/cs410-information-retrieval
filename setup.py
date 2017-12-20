from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='firms',
    version='0.0.9',
    description='Fuzzy Information Retrieval for Musical Scores',
    long_description=long_description,
    url='https://github.com/axiomabsolute/cs410-information-retrieval',
    download_url='https://github.com/axiomabsolute/cs410-information-retrieval/archive/0.0.9.tar.gz',
    author='Devon Terrell',
    author_email='devon@axioms.me',
    license='MIT',
    packages=['firms'],
    python_requires=">=3",
    entry_points={
        'console_scripts': ['firms=firms.command_line:cli'],
    },
    install_requires=[
        'matplotlib',
        'music21',
        'tabulate',
        'click',
        'scipy'
    ])
