SELECT pieces.name, parts.name, snippets.offset, stems.stem, entries.id FROM snippets
LEFT JOIN pieces ON snippets.piece_id=pieces.id
LEFT JOIN parts ON snippets.part_id=parts.id
LEFT JOIN entries ON snippets.id=entries.snippet_id
LEFT JOIN stems ON entries.stem_id = stems.id
WHERE entries.id IS NULL