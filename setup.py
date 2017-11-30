from setuptools import setup

setup(name='firms',
    version='0.0.0',
    description='Fuzzy Information Retrieval for Musical Scores',
    url='https://github.com/axiomabsolute/cs410-information-retrieval',
    author='Devon Terrell',
    author_email='devon@axioms.me',
    license='MIT',
    packages=['firms'],
    install_requirements=[
        'music21',
        'tabulate'
    ])