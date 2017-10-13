from music21 import stream, converter

def wrap_query_as_piece(query):
    piece = stream.Score()
    part = stream.Part()
    part.partName = "query"
    measures = converter.parse("tinynotation: %s" % query)
    for measure in measures:
        part.append(measure)
    piece.append(part)
    return piece