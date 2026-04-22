from stockfish import Stockfish
import os

class TacticalEye:
    def __init__(self, engine_path="./stockfish.exe"):
        print("[*] Initializam ochiul matematic (Stockfish)...")
        
        if not os.path.exists(engine_path):
            raise FileNotFoundError(f"[!] Eroare: Nu am gasit executabilul Stockfish la calea: {engine_path}")
            
        # Initializam motorul. Setam un nivel ridicat pentru analiza
        self.engine = Stockfish(
            path=engine_path,
            depth=18, # Adancime suficienta pentru evaluari rapide (sub 1 secunda)
            parameters={"Threads": 4, "Hash": 256} # Nu ii dam toate cele 32 de nuclee, 4 sunt arhisuficiente pentru o interogare rapida
        )
        print("[V] Stockfish este online si gata de calcul!")

    def analyze_position(self, fen):
        """Primeste un FEN si returneaza matematica pozitiei."""
        self.engine.set_fen_position(fen)
        
        best_move = self.engine.get_best_move()
        evaluation = self.engine.get_evaluation()
        
        # Formatam evaluarea ca sa fie usor de citit (ex: +2.5 sau -M3)
        if evaluation["type"] == "mate":
            eval_string = f"M{evaluation['value']}"
        else:
            # Centipawn (cp) -> impartim la 100 pentru valoarea in pioni
            eval_string = str(evaluation["value"] / 100.0)
            if evaluation["value"] > 0:
                eval_string = "+" + eval_string
                
        return {
            "best_move": best_move,
            "evaluation": eval_string,
            "raw_eval_type": evaluation["type"],
            "raw_eval_value": evaluation["value"]
        }
    def validate_historical_move(self, fen_istoric, mutare_istorica, threshold=0.7):
        """
        Stockfish analizeaza FEN-ul istoric extras din baza de date.
        Verifica daca mutarea jucata de maestru a fost o gafa.
        Returneaza True daca mutarea e buna (drop <= 0.7), False daca e slaba.
        """
        self.engine.set_fen_position(fen_istoric)
        
        # Cerem motorului primele 5 cele mai bune mutari pentru acea pozitie din trecut
        top_moves = self.engine.get_top_moves(5)
        
        if not top_moves:
            return False
            
        # Cat de buna era pozitia teoretic (cea mai buna mutare de calculator)
        best_eval_cp = top_moves[0].get("Centipawn")
        best_mate = top_moves[0].get("Mate")
        
        # Cautam daca mutarea jucata de maestru se afla macar in top 5
        played_move_data = next((m for m in top_moves if m["Move"] == mutare_istorica), None)
        
        if not played_move_data:
            # Daca maestrul a jucat o mutare care nu e nici in top 5 Stockfish, o respingem instant!
            return False
            
        played_eval_cp = played_move_data.get("Centipawn")
        played_mate = played_move_data.get("Mate")
        
        # Tratarea cazurilor de Mat
        if best_mate is not None or played_mate is not None:
            # Daca e mat in 2, dar maestrul a jucat mat in 3, o acceptam.
            # Daca a ratat matul complet, o respingem.
            if played_mate is not None:
                return True
            return False
            
        # Matematica pierderii (Centipawn Loss)
        if best_eval_cp is not None and played_eval_cp is not None:
            # Transformam din centipioni in pioni (ex: 150 cp -> 1.5)
            # In get_top_moves, scorul e mereu relativ la jucatorul care e la mutare (mai mare e mai bine)
            best_score = best_eval_cp / 100.0
            played_score = played_eval_cp / 100.0
            
            # Calculam caderea (cat a pierdut din avantaj prin aceasta mutare)
            drop = best_score - played_score
            
            if drop <= threshold:
                return True # Mutarea e umana, decenta si teoretica!
                
        return False

if __name__ == "__main__":
    # TEST: O pozitie faimoasa cu un sacrificiu real pe h7 (Greek Gift)
    # FEN-ul este de la un meci clasic: Greco vs NN, 1620
    test_fen = "r1bq1rk1/ppp1nppp/2n5/3pP3/1bB1P3/2N2N2/PPP2PPP/R1BQK2R w KQ - 0 1"
    
    # Simulam sacrificiul pe h7 dintr-o alta pozitie standard de atac
    test_fen_greek_gift = "r1bq1rk1/ppp1bppp/2n1pn2/3p2B1/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 1 7"
    
    # Hai sa testam o pozitie evidenta de mat in 1
    test_fen_mate = "rnbqkbnr/ppppp2p/8/5pp1/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3"
    
    ochi = TacticalEye()
    
    print("\n--- Analiza Pozitiei de Mat (Fool's Mate) ---")
    print(f"FEN: {test_fen_mate}")
    rezultat = ochi.analyze_position(test_fen_mate)
    print(f"Mutarea recomandata: {rezultat['best_move']}")
    print(f"Scorul pozitiei: {rezultat['evaluation']}")