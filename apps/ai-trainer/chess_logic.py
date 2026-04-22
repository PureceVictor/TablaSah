import chess

def get_position_fingerprint(fen):
    """
    Analizeaza un FEN si returneaza o amprenta structurala a pozitiei.
    Aceasta amprenta va fi folosita pentru a filtra restrictiv baza de date.
    """
    board = chess.Board(fen)
    fingerprint = {}
    
    # 1. FAZA JOCULUI (Calculam materialul de pe tabla)
    # Ignoram regii si pionii pentru a vedea cate piese grele/usoare mai sunt
    material_count = 0
    for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
        material_count += len(board.pieces(piece_type, chess.WHITE))
        material_count += len(board.pieces(piece_type, chess.BLACK))
        
    if material_count >= 12:
        fingerprint["game_phase"] = "opening_early_mid"
    elif material_count >= 6:
        fingerprint["game_phase"] = "middlegame"
    else:
        fingerprint["game_phase"] = "endgame"
        
    # 2. STATUSUL ROCADEI (Siguranta Regelui)
    # Verificam daca regii si-au parasit pozitia initiala sau au facut rocada
    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)
    
    # e1 este 4, e8 este 60
    w_castled = white_king_sq in [chess.G1, chess.C1] # 6, 2
    b_castled = black_king_sq in [chess.G8, chess.C8] # 62, 58
    
    if w_castled and b_castled:
        # Sunt pe aceeasi parte sau parti opuse?
        if (white_king_sq == chess.G1 and black_king_sq == chess.G8) or \
           (white_king_sq == chess.C1 and black_king_sq == chess.C8):
            fingerprint["king_safety"] = "same_side_castling"
        else:
            fingerprint["king_safety"] = "opposite_side_castling" # Atacuri pe flanc!
    elif w_castled or b_castled:
        fingerprint["king_safety"] = "one_king_castled"
    else:
        fingerprint["king_safety"] = "kings_in_center"

    # 3. TIPUL CENTRULUI (Numaram pionii de pe patratele centrale: d4, e4, d5, e5)
    central_pawns = 0
    for sq in [chess.D4, chess.E4, chess.D5, chess.E5]:
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.PAWN:
            central_pawns += 1
            
    if central_pawns >= 3:
        fingerprint["center_type"] = "closed_or_tense"
    elif central_pawns == 1 or central_pawns == 2:
        fingerprint["center_type"] = "semi_open"
    else:
        fingerprint["center_type"] = "open"

    return fingerprint

if __name__ == "__main__":
    # Testam cu o pozitie complexa de Siciliana (regi pe parti opuse)
    test_fen = "r1bqk2r/pp2bppp/2np1n2/4p3/4P3/1NN1B3/PPP2PPP/R2QKB1R w KQkq - 4 8"
    print(f"Amprenta pentru:\n{test_fen}\n")
    print(get_position_fingerprint(test_fen))