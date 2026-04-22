import json
import time
import chromadb
from chromadb.utils import embedding_functions
from chess_logic import get_position_fingerprint  # <-- Importam logica noastra

def build_vector_database(jsonl_path, db_path="./chess_rag_db"):
    print(f"[*] Initializam baza de date vectoriala (V2 - Amprentata) in: {db_path}")
    
    client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(
        name="chess_master_games",
        embedding_function=sentence_transformer_ef
    )
    
    print("[*] Incepem indexarea datelor cu amprentare logica...")
    
    batch_size = 2000 
    documents = []
    metadatas = []
    ids = []
    
    total_indexed = 0
    start_time = time.time()
    
    with open(jsonl_path, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
                
            doc_text = f"Position analysis: {data['comment']}"
            documents.append(doc_text)
            
            # --- CALCULAM AMPRENTA AICI ---
            try:
                fingerprint = get_position_fingerprint(data["fen"])
            except Exception:
                # Daca FEN-ul e corupt din vreo eroare in PGN-urile originale, dam niste valori default
                fingerprint = {
                    "game_phase": "unknown", 
                    "king_safety": "unknown", 
                    "center_type": "unknown"
                }
            
            # Salvam ADN-ul pozitiei direct in vector!
            metadatas.append({
                "fen": data["fen"],
                "move": data["move"],
                "white": data.get("white", "Unknown"),
                "black": data.get("black", "Unknown"),
                "game_phase": fingerprint["game_phase"],
                "king_safety": fingerprint["king_safety"],
                "center_type": fingerprint["center_type"]
            })
            
            ids.append(f"game_pos_{i}")
            
            if len(documents) >= batch_size:
                collection.add(documents=documents, metadatas=metadatas, ids=ids)
                total_indexed += len(documents)
                documents, metadatas, ids = [], [], []
                elapsed = time.time() - start_time
                print(f"[+] Memorii vectorizate si amprentate: {total_indexed:,} | Timp: {elapsed:.2f} sec")
                
        if documents:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            total_indexed += len(documents)
            
    print(f"\n[V] Baza de date V2 a fost construita cu succes: {total_indexed:,} documente.")

if __name__ == "__main__":
    INPUT_FILE = "training_data_english_only.jsonl" 
    build_vector_database(INPUT_FILE)