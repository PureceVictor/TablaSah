# app/io/pgn_parser.py
import chess.pgn
from app.core.game_manager import Move

class PGNParser:
    @staticmethod
    def load_pgn_to_gamestate(file_path, game_state):
        """
        Citeste un fisier PGN si injecteaza mutarile in GameState-ul nostru.
        Returneaza metadatele (Nume jucatori, ELO, Data etc.)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as pgn_file:
                # Folosim python-chess doar pentru a citi textul
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    return None
                    
                headers = dict(game.headers)
                
                # Dictionare pentru traducerea coordonatelor in indecsii matricei noastre
                files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
                ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}

                # Parcurgem linia principala a meciului din fisier
                for move in game.mainline_moves():
                    uci_str = move.uci() # Format Universal: 'e2e4', 'g1f3', 'e7e8q'
                    
                    start_col = files_to_cols[uci_str[0]]
                    start_row = ranks_to_rows[uci_str[1]]
                    end_col = files_to_cols[uci_str[2]]
                    end_row = ranks_to_rows[uci_str[3]]
                    
                    # Daca are 5 caractere, ultimul este promovarea (ex: 'q', 'r', 'n', 'b')
                    promotion_choice = uci_str[4].upper() if len(uci_str) == 5 else 'Q'
                    
                    # 1. Cerem motorului TOATE mutarile valide din acea secunda
                    valid_moves = game_state.allValidMoves()
                    
                    # 2. Cautam mutarea noastra care se potriveste cu coordonatele din PGN
                    move_applied = False
                    for v_move in valid_moves:
                        if (v_move.startRow == start_row and v_move.startCol == start_col and 
                            v_move.endRow == end_row and v_move.endCol == end_col):
                            
                            # Daca e promovare, trebuie sa se potriveasca si piesa aleasa
                            if v_move.isPawnPromotion:
                                if v_move.promotionChoice == promotion_choice:
                                    game_state.makeMove(v_move)
                                    move_applied = True
                                    break
                            else:
                                game_state.makeMove(v_move)
                                move_applied = True
                                break
                                
                    if not move_applied:
                        print(f"[EROARE PARSER] Mutarea {uci_str} din PGN a fost considerata ILEGALA de motorul nostru!")
                        break # Oprim parsarea daca motorul nostru refuza o mutare
                        
                # La final, derulam motorul inapoi la inceput, ca userul sa poata naviga cu sagetile
                while game_state.current_node.parent is not None:
                    game_state.undoMove()
                    
                return headers

        except FileNotFoundError:
            print(f"Fisierul nu a fost gasit: {file_path}")
            return None
        except Exception as e:
            print(f"Eroare la parsarea PGN: {e}")
            return None