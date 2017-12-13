from firms.models import IRSystem, FirmIndex, get_part_details, get_snippets_for_part, print_timing
import sqlite3

class SqlIRSystem(IRSystem):

    def __init__(self, dbpath, index_methods, graders = None, piece_paths = [], rebuild = True):
        # Ensure pieces, stemmers, snippets, parts, stems, and entries tables exist
        # Add each index method to stemmers table
        self.dbpath = dbpath
        with sqlite3.connect(self.dbpath) as conn:
            self.ensure_db(conn)
            self.stemmer_ids = self.ensure_stemmers(index_methods, conn)
        super().__init__(index_methods, graders, piece_paths, rebuild)

    def makeEmptyIndex(self, indexfn, name):
        return SqlIndex(self.dbpath, [], indexfn, name, self.stemmer_ids[name])

    def add_piece(self, piece, piece_path):
        with sqlite3.connect(self.dbpath) as conn:
            with conn.cursor() as cursor:
                cursor.execute("PRAGMA synchronous = OFF")
                cursor.execute("PRAGMA journal_mode = OFF")
                piece_id = None
                for part in get_part_details(piece):
                    piece_name = part.piece
                    part_name = part.name
                    if not piece_id:
                        piece_id = self.ensure_piece(piece_path, piece_name, conn, cursor)
                    part_id = self.ensure_part(piece_id, part_name, conn, cursor)
                    snippets = list(get_snippets_for_part(part))
                    snippet_ids = self.ensure_snippets(snippets, piece_id, part_id, conn, cursor)
                    for idx in self.indexes.values():
                        idx.add_snippets(snippets, snippet_ids, conn, cursor)

    def ensure_db(self, conn):
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS pieces (id INTEGER PRIMARY KEY ASC,
                                                path TEXT NOT NULL,
                                                name TEXT NOT NULL
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS parts (id INTEGER PRIMARY KEY ASC,
                                                piece_id INTEGER NOT NULL,
                                                name TEXT NOT NULL,
                        FOREIGN KEY (piece_id) REFERENCES pieces(id))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS stemmers (id INTEGER PRIMARY KEY ASC,
                                                    name TEXT NOT NULL
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS snippets (id INTEGER PRIMARY KEY ASC,
                                                    piece_id INTEGER NOT NULL,
                                                    part_id INTEGER NOT NULL,
                                                    offset INTEGER NOT NULL,
                                                    FOREIGN KEY (part_id) REFERENCES parts(id),
                                                    FOREIGN KEY (piece_id) REFERENCES pieces(id),
                                                    CONSTRAINT unique_snippet UNIQUE (piece_id, part_id, offset)
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS stems (id INTEGER PRIMARY KEY ASC,
                                                stemmer_id INTEGER NOT NULL,
                                                stem TEXT NOT NULL,
                                                FOREIGN KEY (stemmer_id) REFERENCES stemmers(id),
                                                CONSTRAINT unique_stem UNIQUE (stemmer_id, stem)
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY ASC,
                                                stem_id INTEGER NOT NULL,
                                                snippet_id INTEGER NOT NULL,
                                                FOREIGN KEY (stem_id) REFERENCES stems(id),
                                                FOREIGN KEY (snippet_id) REFERENCES snippets(id),
                                                CONSTRAINT unique_entry UNIQUE (stem_id, snippet_id)
                        )""")
        conn.commit()
        cursor.execute("""CREATE INDEX IF NOT EXISTS piece_path_idx ON pieces(path)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS stemmer_name_idx ON stemmers(name)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS snippet_piece_idx ON snippets(piece_id)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS snippet_part_idx ON snippets(part_id)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS part_piece_idx ON parts(piece_id)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS stem_stemmer_idx ON stems(stemmer_id)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS stem_stem_idx ON stems(stem)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS entry_stem_idx ON entries(stem_id)""")

    def ensure_stemmers(self, stemmers, conn):
        cursor = conn.cursor()
        stemmer_ids = {}
        for stemmer_name in stemmers.keys():
            cursor.execute("SELECT id FROM stemmers WHERE name=?", (stemmer_name, ))
            results = cursor.fetchall()
            if not results:
                cursor.execute("INSERT INTO stemmers (name) VALUES (?)", (stemmer_name, ))
            stemmer_ids[stemmer_name] = cursor.lastrowid
        conn.commit()
        return stemmer_ids

    def ensure_piece(self, piece_path, piece_name, conn, cursor):
        cursor.execute("SELECT id FROM pieces WHERE path=? AND name=? LIMIT 1",
            (piece_path, piece_name)
        )
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO pieces (path, name) VALUES (?, ?)",
            (piece_path, piece_name)
        )
        conn.commit()
        return cursor.lastrowid

    def ensure_part(self, piece_id, part_name, conn, cursor):
        cursor.execute("SELECT id FROM parts WHERE piece_id=? AND name=? LIMIT 1", (piece_id, part_name))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO parts (piece_id, name) VALUES (?, ?)", (piece_id, part_name))
        conn.commit()
        return cursor.lastrowid

    def ensure_snippet(self, snippet, piece_id, part_id, conn, cursor):
        cursor.execute("SELECT id FROM snippets WHERE piece_id=? AND part_id=? AND offset=?", (piece_id, part_id, snippet.offset))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO snippets (piece_id, part_id, offset) VALUES (?, ?, ?)", (piece_id, part_id, snippet.offset))
        conn.commit()
        return cursor.lastrowid

    def ensure_snippets(self, snippets, piece_id, part_id, conn, cursor):
        values = [ (piece_id, part_id, snippet.offset) for snippet in snippets ]
        cursor.executemany("INSERT OR IGNORE INTO snippets (piece_id, part_id, offset) VALUES (?, ?, ?)", values)
        conn.commit()
        cursor.execute("SELECT id FROM snippets WHERE piece_id=? AND part_id=?", (piece_id, part_id))
        return [r[0] for r in cursor.fetchall()]

    def get_number_of_pieces(self):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute("""SELECT count(*) FROM pieces""")
        result = cursor.fetchone()
        conn.close()
        return result[0]

    def lookup(self, snippet):
        conn = sqlite3.connect(self.dbpath) 
        cursor = conn.cursor()
        return super().lookup(snippet, conn, cursor)

    def raw_query(self, query, *args):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        return super().raw_query(query, conn, cursor, *args)

    def corpus_size(self):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM pieces")
        result = cursor.fetchone()
        return result[0]

    def piece_by_id(self, id):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pieces WHERE pieces.id=?", (id, ))
        return cursor.fetchall()

    def pieces(self):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute("SELECT name, path, id FROM pieces")
        return cursor.fetchall()

    def stemmers(self):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stemmers")
        return cursor.fetchall()

    def graders(self):
        return self.grader_methods.keys()

    def info(self):
        tables = ["entries", "pieces", "parts", "snippets", "stems", "stemmers"]
        results = {}
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        print(cursor.arraysize)
        for table in tables:
            cursor.execute("SELECT count(*) FROM %s" % table)
            results[table] = cursor.fetchone()[0]
        return results

class SqlIndex(FirmIndex):
    def __init__(self, dbpath, snippets, keyfn, name, stemmer_id):
        self.dbpath = dbpath
        self.stemmer_id = stemmer_id
        super().__init__(snippets, keyfn, name)
    
    def ensure_stem(self, stemmer_id, stem, conn, cursor):
        cursor.execute("SELECT id FROM stems WHERE stemmer_id=? AND stem=? LIMIT 1", (stemmer_id, stem))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO stems (stemmer_id, stem) VALUES (?, ?)", (stemmer_id, stem))
        conn.commit()
        return cursor.lastrowid

    def ensure_entry(self, stem_id, snippet_id, conn, cursor):
        cursor.execute("SELECT id FROM entries WHERE stem_id=? AND snippet_id=? LIMIT 1", (stem_id, snippet_id))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO entries (stem_id, snippet_id) VALUES (?, ?)", (stem_id, snippet_id))
        conn.commit()
        return cursor.lastrowid
    
    def ensure_entries(self, stem_ids, snippet_ids, conn, cursor):
        values = list(zip(stem_ids, snippet_ids))
        cursor.executemany("INSERT OR IGNORE INTO entries (stem_id, snippet_id) VALUES (?, ?)", values)
        conn.commit()
        return [r[0] for value in values for r in cursor.execute("SELECT id FROM entries WHERE stem_id=? AND snippet_id=? LIMIT 1", value)]

    def ensure_stems(self, stemmer_id, stems, conn, cursor):
        values = [ (stemmer_id, stem) for stem in stems ]
        cursor.executemany("INSERT OR IGNORE INTO stems (stemmer_id, stem) VALUES (?, ?)", values)
        conn.commit()
        return [r[0] for value in values for r in cursor.execute("SELECT id FROM stems WHERE stemmer_id=? AND stem=? LIMIT 1", value)]

    def add_snippets(self, snippets, snippet_ids, conn, cursor):
        stems = [self.keyfn(snippet)[0] for snippet in snippets]
        stem_ids = self.ensure_stems(self.stemmer_id, stems, conn, cursor)
        return self.ensure_entries(stem_ids, snippet_ids, conn, cursor)

    def add_snippet(self, snippet, snippet_id, conn, cursor):
        stems = self.keyfn(snippet)
        for stem in stems:
            stem_id = self.ensure_stem(self.stemmer_id, stem, conn, cursor)
            entry_id = self.ensure_entry(stem_id, snippet_id, conn, cursor)
        return entry_id

    def lookup(self, snippet, conn, cursor):
        stems = self.keyfn(snippet)
        for stem in stems:
            cursor.execute("""SELECT snippets.id, pieces.name, snippets.part_id as part, snippets.offset, stems.id, pieces.path, pieces.id FROM snippets
                            JOIN entries ON entries.snippet_id=snippets.id
                            JOIN stems ON stems.id=entries.stem_id
                            JOIN pieces ON pieces.id=snippets.piece_id
                            WHERE stems.stem=?""", (stem, ))
        results = cursor.fetchall()
        return [ {'id': r[0], 'piece': r[5], 'part': r[2], 'offset': r[3], 'stem': r[4], 'path': r[5], 'piece_id': r[6]} for r in results ]
