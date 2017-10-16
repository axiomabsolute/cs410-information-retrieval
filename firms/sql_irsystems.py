from firms.models import IRSystem, FirmIndex, get_part_details
import sqlite3

class SqlIRSystem(IRSystem):

    def __init__(self, dbpath, index_table_names, index_methods, scorers = None, piece_paths = []):
        # Ensure pieces, stemmers, snippets, parts, stems, and entries tables exist
        # Add each index method to stemmers table
        self.dbpath = dbpath
        self.index_table_names = index_table_names
        conn = sqlite3.connect(self.dbpath)
        self.ensure_db(conn)
        super().__init__(index_methods, scorers, piece_paths)
        conn.close()

    def makeEmptyIndex(self, indexfn, name):
        return SqlIndex(self.dbpath, self.index_table_names[name], [], indexfn, name)

    def add_piece(self, piece, piece_path):
        # Ensure piece in pieces table
        # Extract snippets
        # Ensure exist in snipets table
        # Ensure parts exist
        # For each index method
        ## Ensure stem exists
        ## Ensure entry exists
        conn = sqlite3.connect(self.dbpath)
        pieces = set()
        for part in get_part_details(piece):
            if part[0] not in pieces:
                try:
                    self.ensure_piece(piece_path, part, conn)
                    pieces.add(part[0])
                except:
                    print(part)

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
                                                    FOREIGN KEY (piece_id) REFERENCES pieces(id)
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS stems (id INTEGER PRIMARY KEY ASC,
                                                stemmer_id INTEGER NOT NULL,
                                                stem TEXT NOT NULL,
                                                FOREIGN KEY (stemmer_id) REFERENCES stemmers(id)
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY ASC,
                                                stem_id INTEGER NOT NULL,
                                                snippet_id INTEGER NOT NULL,
                                                FOREIGN KEY (stem_id) REFERENCES stems(id),
                                                FOREIGN KEY (snippet_id) REFERENCES snippets(id)
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
    
    def ensure_piece(self, piece_path, piece, conn):
        piece_name = piece[0].replace('\'', '')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pieces WHERE path='{path}' AND name='{name}' LIMIT 1".format(
            path=piece_path, name=piece_name
        ))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        cursor.execute("INSERT INTO pieces (path, name) VALUES (?, ?)",
            (piece_path, piece_name)
        )
        conn.commit()
        return cursor.lastrowid

class SqlIndex(FirmIndex):
    def __init__(self, dbpath, table_name, snippets, keyfn, name = ""):
        self.dbpath = dbpath
        self.table_name = table_name
        # Ensure stemmer exists in stemmers table
        super().__init__(snippets, keyfn, name)

    def add_snippet(self, snippet):
        conn = sqlite3.connect(self.dbpath)
        # Ensure piece in pieces table
        # Ensure snippet in snippets table
        # Ensure part in parts table
        # Ensure stem in stem table
        # Ensure entry in entries table

    def add_snippets(self, snippets):
        # May want to override this - piece/snippet/part checks only need to happen once
        super().add_snippets(snippets)

    def lookup(self, snippet):
        pass