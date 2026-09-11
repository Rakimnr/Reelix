import sqlite3
import os

class CatalogueBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS tracks (
                        track_id TEXT PRIMARY KEY,
                        title TEXT,
                        duration REAL
                    )''')
                    
        c.execute('''CREATE TABLE IF NOT EXISTS fingerprints (
                        hash TEXT,
                        offset INTEGER,
                        track_id TEXT,
                        FOREIGN KEY(track_id) REFERENCES tracks(track_id)
                    )''')
                    
        c.execute('''CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints(hash)''')
        conn.commit()
        conn.close()

    def add_track(self, track_id: str, title: str, duration: float, hashes: list):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Upsert track
        c.execute("INSERT OR REPLACE INTO tracks (track_id, title, duration) VALUES (?, ?, ?)", 
                  (track_id, title, duration))
        
        # Remove old fingerprints for this track (if re-indexing)
        c.execute("DELETE FROM fingerprints WHERE track_id = ?", (track_id,))
        
        # Insert hashes
        records = [(h[0], h[1], track_id) for h in hashes]
        c.executemany("INSERT INTO fingerprints (hash, offset, track_id) VALUES (?, ?, ?)", records)
        
        conn.commit()
        conn.close()
        
    def get_track_info(self, track_id: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT title, duration FROM tracks WHERE track_id = ?", (track_id,))
        res = c.fetchone()
        conn.close()
        if res:
            return {"title": res[0], "duration": res[1]}
        return None
        
    def find_matches(self, hashes: list):
        """
        Takes a list of (hash_str, offset) from a query.
        Returns matched records from DB.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # We need to query many hashes. Batch query.
        hash_strings = list(set([h[0] for h in hashes]))
        
        # SQLite IN clause limit is 999. Batch it.
        chunk_size = 900
        all_matches = []
        
        for i in range(0, len(hash_strings), chunk_size):
            chunk = hash_strings[i:i+chunk_size]
            placeholders = ','.join(['?'] * len(chunk))
            query = f"SELECT hash, offset, track_id FROM fingerprints WHERE hash IN ({placeholders})"
            c.execute(query, chunk)
            all_matches.extend(c.fetchall())
            
        conn.close()
        return all_matches
