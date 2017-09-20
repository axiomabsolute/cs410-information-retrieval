Project Idea: Searching Musical Scores

Tags: project_idea

Due to some awkwardness in my work and travel schedule over the next several months, I intend to work on this project alone - as a team of 1.

Project Description
===================

This project explores how concepts in textual information retrieval can be applied to efficiently index and search for musical scores. I intend to focus on two particular use-cases:

1. A listener searching for a specific piece by trying to reproduce a small section by ear.
2. A composer interested in surveying pieces which feature similar themes.

Both use-cases require a flexible IR system.

In the first case, listeners are generally not able to exactly reproduce music by ear (e.g. to exactly match tempo, identify pitches, or detect rythm). Furthermore, there is often some ambiguity in notation (e.g. a quarter and half note sound like they are the same length if the tempo is two times as fast for the half note).

In the second case, the goal is explicitly *not* to find exact matches, but rather to find variations of the provided theme. Variation can occur rhythmically (stretching, compressing, or changing rythm while maintaining pitches), tonally (by shifting pitch, changing keys, inversions, etc), or more broadly may simply follow the same contour or chord progression.

Technology Review
==================

One of many unique challenges of indexing and analyzing music is simply how to represent and manipulate it digitally. Traditionally, musical notation has been designed and optimized to enable performers to accurately perform musical works in real-time. As a result, the notation tends to be very dense and rely on contextual clues and training to reduce the amount of information which needs to be read in real time. Early digital representations of music were focused on either streaming for playback or on notational aspects for typesetting musical scores. For the technology review, I will be looking at methods of digitally representing music that are appropriate for indexing by various dimensions and which lend themselves to programmatic manipulation. In particularly, I will look at the following:

1. MIDI - Standard
2. MusicXML - Standard
3. Humdrum Syntax - Ohio State's Cognitive Systematic Musicology Lab
4. Lilypond Notation (Alda - microlanguage derived from Lilypond)
5. Abjad - Open source python library for music notation and analysis
6. music21 - from MIT's computational musicology group

Existing Work
=============

An overview of the challenges and techniques used in music information retrieval can be found in

> Orio N. (2008) Music Indexing and Retrieval for Multimedia Digital Libraries. In: Agosti M. (eds) Information Access through Search Engines and Digital Libraries. The Information Retrieval Series, vol 22. Springer, Berlin, Heidelberg

The International Society for Music Information Retrieval (ISMIR) provides [many additional resources](http://www.ismir.net/resources.php) for working with music information retrieval, including software packages, data sets, and educational materials.