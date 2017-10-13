Technology Review
==================

My technology review will cover some of the unique challenges of building a vertical search engine covering musical notation.

One of many unique challenges of indexing and analyzing music is simply how to represent and manipulate it digitally. Traditionally, musical notation has been designed and optimized to enable performers to accurately perform musical works in real-time. As a result, the notation tends to be very dense and rely on contextual clues and training to reduce the amount of information which needs to be read in real time. Early digital representations of music were focused on either streaming for playback or on notational aspects for typesetting musical scores. For the technology review, I will be looking at methods of digitally representing music that are appropriate for indexing by various dimensions and which lend themselves to programmatic manipulation and analysis. In particularly, I will look at the following:

1. MIDI - Standard streaming playback format
2. MusicXML - Standardized XML based format
3. Humdrum Syntax - Ohio State's Cognitive Systematic Musicology Lab
4. Scala - Experimental music notation
5. TinyNotation - Highly simplified, single line format derived from Lilypond

In addition, the technology review will go over the basics of the primary tool used for analysis and development of the IR system: the `music21` Python library, developed by MIT's computational musicology group. 

Existing Work
=============

An overview of the challenges and techniques used in music information retrieval can be found in

> Orio N. (2008) Music Indexing and Retrieval for Multimedia Digital Libraries. In: Agosti M. (eds) Information Access through Search Engines and Digital Libraries. The Information Retrieval Series, vol 22. Springer, Berlin, Heidelberg

The International Society for Music Information Retrieval (ISMIR) provides [many additional resources](http://www.ismir.net/resources.php) for working with music information retrieval, including software packages, data sets, and educational materials.