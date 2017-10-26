select parts.piece_id, parts.name, stems.stem from parts
JOIN snippets on snippets.part_id=parts.id
JOIN entries on entries.snippet_id=snippets.id
JOIN stems on entries.stem_id=stems.id
AND stems.stemmer_id=1
AND stems.stem LIKE "%[%"