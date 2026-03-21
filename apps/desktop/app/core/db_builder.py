# app/core/db_builder.py
import os
import sqlite3
import chess.pgn
from PyQt6.QtCore import QThread, pyqtSignal

class DatabaseBuilderWorker(QThread):
    # Semnale pentru a comunica cu interfata grafica (fara sa o blocheze)
    progress = pyqtSignal(int, str) # Trimite procentajul (0-100) si textul
    finished = pyqtSignal(str)      # Trimite calea catre noul fisier .db
    error = pyqtSignal(str)         # In caz ca apare vreo problema

    def __init__(self, pgn_path):
        super().__init__()
        self.pgn_path = pgn_path
        # Fisierul nostru de indexare se va numi ex: "Mega2019.pgn.db"
        self.db_path = pgn_path + ".db" 
        self.is_cancelled = False

    def run(self):
        try:
            total_size = os.path.getsize(self.pgn_path)
            
            # 1. Conectare la SQLite (creeaza fisierul automat)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 2. Curatam daca exista deja o incercare esuata si cream tabelul curat
            cursor.execute("DROP TABLE IF EXISTS games")
            cursor.execute("""
                CREATE TABLE games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    white TEXT,
                    black TEXT,
                    white_elo TEXT,
                    black_elo TEXT,
                    result TEXT,
                    date TEXT,
                    event TEXT,
                    byte_offset INTEGER
                )
            """)
            
            # --- SECRETUL VITEZEI SUPREME IN SQLITE ---
            # Oprim masurile de siguranta la scriere pe disc (crash-proof) pentru a mari viteza de 10x
            # Deoarece doar citim dintr-un PGN, daca pica curentul, pur si simplu stergem .db si refacem.
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = MEMORY")
            
            games_batch = []
            batch_size = 50000 # Nu scriem fiecare meci pe hard disk, ci in pachete de 50.000!
            games_count = 0
            
            # 3. Deschidem monstrul de fisier
            with open(self.pgn_path, "r", encoding="latin-1") as f:
                while not self.is_cancelled:
                    offset = f.tell()
                    
                    # Citim rapid doar headerele
                    headers = chess.pgn.read_headers(f)
                    if headers is None:
                        break # Gata, am ajuns la finalul celor 7.2 GB
                        
                    # Punem datele in pachet
                    games_batch.append((
                        headers.get("White", "?"),
                        headers.get("Black", "?"),
                        headers.get("WhiteElo", ""),
                        headers.get("BlackElo", ""),
                        headers.get("Result", "*"),
                        headers.get("Date", "????.??.??"),
                        headers.get("Event", "?"),
                        offset
                    ))
                    
                    games_count += 1
                    
                    # 4. Cand s-a umplut pachetul (50.000 meciuri), scriem tot dintr-un foc in SQLite
                    if len(games_batch) >= batch_size:
                        cursor.executemany("""
                            INSERT INTO games (white, black, white_elo, black_elo, result, date, event, byte_offset) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, games_batch)
                        conn.commit()
                        games_batch = [] # Golim pachetul
                        
                        # 5. Calculam unde suntem si updatam UI-ul
                        percent = int((offset / total_size) * 100)
                        self.progress.emit(percent, f"Indexate: {games_count:,} meciuri...")
                        
            # Inseram ultimele meciuri ramase in pachet (< 50.000)
            if games_batch and not self.is_cancelled:
                cursor.executemany("""
                    INSERT INTO games (white, black, white_elo, black_elo, result, date, event, byte_offset) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, games_batch)
                conn.commit()
            
            # 6. Cream INDECSI pentru Search (asta te va lasa sa cauti jucatori instant)
            if not self.is_cancelled:
                self.progress.emit(99, "Se construiesc indecsii de cautare ultra-rapida...")
                cursor.execute("CREATE INDEX idx_white ON games(white)")
                cursor.execute("CREATE INDEX idx_black ON games(black)")
            
            conn.close()
            
            # Trimitem semnalul de finalizare!
            if not self.is_cancelled:
                self.progress.emit(100, f"Finalizat! Total: {games_count:,} meciuri.")
                self.finished.emit(self.db_path)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def cancel(self):
        """Opreste fortat scanarea daca utilizatorul se razgandeste"""
        self.is_cancelled = True