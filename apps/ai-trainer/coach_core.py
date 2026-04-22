import chromadb
from chromadb.utils import embedding_functions
from chess_engine import TacticalEye 
from chess_logic import get_position_fingerprint  # <-- Importul noului nostru senzor de structura

class ChessCoachCore:
    def __init__(self):
        print("[*] Se porneste Antrenorul AI...")
        
        # 1. Initiem Ochiul Matematic (Stockfish)
        self.ochi = TacticalEye()
        
        # 2. Initiem Memoria (RAG / ChromaDB)
        print("[*] Se incarca memoria vectoriala AMPRENTATA...")
        self.chroma_client = chromadb.PersistentClient(path="./chess_rag_db")
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_collection(
            name="chess_master_games",
            embedding_function=self.sentence_transformer_ef
        )
        print("[V] Sistem complet online. Astept pozitii (FEN).")

    def consult(self, fen):
        print(f"\n" + "="*50)
        print(f"Analizez FEN-ul: {fen}")
        print("="*50)
        
        # PASUL 1: Intrebam Stockfish-ul
        analiza = self.ochi.analyze_position(fen)
        best_move = analiza["best_move"]
        evaluare = analiza["evaluation"]
        
        print(f"\n[Stockfish] Evaluare: {evaluare} | Mutare optima: {best_move}")
        
        # PASUL 2: Extragem amprenta structurala a FEN-ului curent
        amprenta = get_position_fingerprint(fen)
        print(f"[*] Amprenta structurii curente: Faza={amprenta['game_phase']}, Centru={amprenta['center_type']}")
        
        # PASUL 3: Formulăm o intrebare inteligenta pentru RAG cu filtru STRICT
        query_text = "Explain the tactical advantage, king safety, or positional concept behind this move."
        
        print(f"[*] Interoghez memoria... Aplic filtru pe mutarea '{best_move}' si geometria tablei...")
        
        try:
            # Folosim operatorul $and pentru a forta ChromaDB sa respecte toate conditiile
            results = self.collection.query(
                query_texts=[query_text],
                n_results=2, 
                where={
                    "$and": [
                        {"move": best_move},
                        {"game_phase": amprenta["game_phase"]},
                        {"center_type": amprenta["center_type"]}
                    ]
                }
            )
            
            # Afisam rezultatele
            print("\n[Memorie Istorica - Rezultate RAG]")
            if not results['documents'][0]:
                print("[!] Nu am gasit explicatii istorice pentru aceasta combinatie exacta de mutare si structura.")
            else:
                referinte_valide = 0
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    fen_istoric = meta['fen']
                    mutare_istorica = meta['move']
                    
                    # === AICI E BARIERA TA DE 2000 ELO ===
                    print(f"[*] Validez Referinta {i+1} in culise (Mutare istorica: {mutare_istorica})...")
                    is_valid = self.ochi.validate_historical_move(fen_istoric, mutare_istorica, threshold=0.7)
                    
                    if not is_valid:
                        print(f"  [X] Referinta respinsa! Maestrul a facut o gafa (sau o mutare slaba) in trecut. O stergem din memorie.")
                        continue # Sarim peste acest document fals!
                    
                    # Daca a trecut testul, o afisam/folosim
                    referinte_valide += 1
                    lichess_url = f"https://lichess.org/analysis/standard/{fen_istoric.replace(' ', '_')}"
                    
                    print(f"\n--- Referinta Valida {referinte_valide} ---")
                    print(f"Structura: Faza={meta.get('game_phase')}, Centru={meta.get('center_type')}")
                    print(f"Mutare jucata: {mutare_istorica}")
                    print(f"Explicatie sigura: {doc}")
                    print(f"Link Tabla: {lichess_url}")
                    
                if referinte_valide == 0:
                    print("\n[!] Toate comentariile gasite de AI explicau mutari proaste. Stockfish le-a respins pe toate pentru siguranta ta.")
                    
        except Exception as e:
            print(f"[!] Eroare la interogarea bazei de date: {e}")
            results = None # Returnam None daca pica filtrarea
            
        return analiza, results

    
if __name__ == "__main__":
    # Instantiem antrenorul
    coach = ChessCoachCore()
    
    # Test: Pozitie complexa (Apararea Franceza)
    test_fen = "r1b1k2r/pp2bppp/1qn1p3/3pP3/3P4/P1N1PN2/1P1QB1PP/R3K2R w KQkq - 1 12"
    
    coach.consult(test_fen)