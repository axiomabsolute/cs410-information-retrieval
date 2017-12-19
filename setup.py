from setuptools import setup

setup(
    name='firms',
    version='0.0.6',
    description='Fuzzy Information Retrieval for Musical Scores',
    url='https://github.com/axiomabsolute/cs410-information-retrieval',
    download_url='https://github.com/axiomabsolute/cs410-information-retrieval/archive/0.0.6.tar.gz',
    author='Devon Terrell',
    author_email='devon@axioms.me',
    license='MIT',
    packages=['firms'],
    python_requires=">=3",
    entry_points={
        'console_scripts': ['firms=firms.command_line:main'],
    },
    install_requires=[
        'music21',
        'tabulate',
        'click',
        'scipy'
    ])
