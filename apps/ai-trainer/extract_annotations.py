import chess.pgn
import json
import os
import time
import re
import io
import multiprocessing
from langdetect import detect, LangDetectException

# --- FUNCTIILE MUNCITORULUI ---

def clean_chessbase_tags(text):
    clean = re.sub(r'\[%.*?\]', '', text)
    return " ".join(clean.split())

def process_game_batch(raw_games_batch):
    results = []
    
    for raw_game_text in raw_games_batch:
        game = chess.pgn.read_game(io.StringIO(raw_game_text))
        if game is None:
            continue
            
        # Filtrul 1: ELO
        if "WhiteElo" not in game.headers or "BlackElo" not in game.headers:
            continue
            
        try:
            # Vrem partide tari, dar ignoram erorile de formatare
            w_elo = int(game.headers.get("WhiteElo", "0").replace('?', '0'))
            b_elo = int(game.headers.get("BlackElo", "0").replace('?', '0'))
            if w_elo < 2100 and b_elo < 2100:
                continue
        except ValueError:
            continue

        board = game.board()
        for node in game.mainline():
            raw_comment = node.comment.strip()
            
            # Filtrul 2: Minim 25 caractere
            if raw_comment and len(raw_comment) >= 25:
                clean_comment = clean_chessbase_tags(raw_comment)
                
                try:
                    lang = detect(clean_comment)
                except LangDetectException:
                    lang = "unknown"
                    
                data_point = {
                    "fen": board.fen(),
                    "move": node.move.uci(),
                    "comment": clean_comment,
                    "lang": lang,
                    "white": game.headers.get("White", "Unknown"),
                    "black": game.headers.get("Black", "Unknown"),
                    "event": game.headers.get("Event", "Unknown")
                }
                results.append(data_point)
                
            board.push(node.move)
            
    return results

# --- DISPECERUL ---

def game_batch_generator(pgn_path, batch_size=1000):
    batch = []
    current_game_lines = []
    
    with open(pgn_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("[Event ") and current_game_lines:
                batch.append("".join(current_game_lines))
                current_game_lines = [line]
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            else:
                current_game_lines.append(line)
                
        if current_game_lines:
            batch.append("".join(current_game_lines))
        if batch:
            yield batch

def mine_megadatabase_fast(pgn_path, output_jsonl_path):
    print(f"[*] Lansam modul Multi-Core (Streaming curat) pe: {pgn_path}")
    
    max_workers = max(1, multiprocessing.cpu_count() - 2)
    print(f"[*] Nuclee activate: {max_workers}")
    
    start_time = time.time()
    total_batches_processed = 0
    total_comments_saved = 0
    batch_size = 1000 
    
    with open(output_jsonl_path, "w", encoding="utf-8") as out_file:
        # Folosim Pool.imap_unordered pentru a nu bloca memoria RAM!
        with multiprocessing.Pool(processes=max_workers) as pool:
            batches = game_batch_generator(pgn_path, batch_size)
            
            # Tragem din generator DOAR cand un nucleu e liber
            for results in pool.imap_unordered(process_game_batch, batches):
                total_batches_processed += 1
                
                for res in results:
                    out_file.write(json.dumps(res) + "\n")
                    total_comments_saved += 1
                
                # Feedback rapid la fiecare 5 pachete (5.000 partide)
                if total_batches_processed % 5 == 0:
                    elapsed = time.time() - start_time
                    partide_scanate = total_batches_processed * batch_size
                    print(f"[+] Partide trimise la nuclee: ~{partide_scanate:,} | Extrase: {total_comments_saved:,} | Timp: {elapsed:.2f} sec")

    final_time = time.time() - start_time
    print(f"\n[V] Minerit Multi-Core Finalizat in {final_time:.2f} secunde!")
    print(f"Total comentarii extrase: {total_comments_saved:,}")

if __name__ == "__main__":
    MEGA_DB_PATH = "C:/Users/victo/Documents/ChessBase/MyWork/MegaDatabase2019.pgn" 
    OUTPUT_PATH = "training_data_multilingual.jsonl"
    
    multiprocessing.freeze_support() 
    
    if os.path.exists(MEGA_DB_PATH):
        mine_megadatabase_fast(MEGA_DB_PATH, OUTPUT_PATH)
    else:
        print(f"[X] Eroare fisier")