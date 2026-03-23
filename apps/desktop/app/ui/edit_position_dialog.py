# app/ui/edit_position_dialog.py
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QRadioButton, QButtonGroup, 
                             QCheckBox, QGroupBox, QWidget)
from PyQt6.QtGui import QPixmap, QIcon, QCursor
from PyQt6.QtCore import Qt, QSize

# O clasa mica pentru patratele de pe tabla noastra de editare
class EditSquare(QLabel):
    def __init__(self, row, col, dialog_parent):
        super().__init__()
        self.row = row
        self.col = col
        self.dialog = dialog_parent
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Coloram tabla (alternant)
        is_light = (row + col) % 2 == 0
        color = "#f0d9b5" if is_light else "#b58863"
        self.setStyleSheet(f"background-color: {color};")
        self.piece = "--"

    # Cand dam click pe ea, aplicam "stampila" curenta
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dialog.apply_stamp(self.row, self.col)

class EditPositionDialog(QDialog):
    def __init__(self, current_fen=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editare Pozitie (Board Setup)")
        self.setFixedSize(950, 550)
        
        # Starea interna a tablei (8x8)
        self.board = [["--" for _ in range(8)] for _ in range(8)]
        self.current_stamp = "--" # Implicit e guma de sters
        
        # Calea catre imagini
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        self.images_dir = os.path.join(base_dir, "assets", "pieces")
        
        self.setup_ui()
        if current_fen:
            self.load_fen(current_fen) # Daca avem deja piese pe tabla, le incarcam
        else:
            self.load_starting_position()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)


        #Zona stanga
        board_container = QWidget()
        board_container.setFixedSize(480, 480) # Fortam tabla sa fie un patrat perfect (8 * 60)
        self.grid = QGridLayout(board_container)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0) # TAIEM SPATIILE DINTRE PATRATE
        
        self.squares = []
        for r in range(8):
            row_squares = []
            for c in range(8):
                sq = EditSquare(r, c, self)
                self.grid.addWidget(sq, r, c)
                row_squares.append(sq)
            self.squares.append(row_squares)
            
        main_layout.addWidget(board_container)
        
        # --- ZONA DREAPTA: Controale si Paleta ---
        right_panel = QWidget()
        right_panel.setFixedWidth(400)
        right_layout = QVBoxLayout(right_panel)
        
        # 1. Butoane de Actiune
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("🗑️ Clear Board")
        btn_clear.clicked.connect(self.clear_board)
        btn_start = QPushButton("♟️ Start Position")
        btn_start.clicked.connect(self.load_starting_position)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_start)
        right_layout.addLayout(btn_layout)
        
        # 2. Paleta de piese (Stampilele)
        palette_group = QGroupBox("Paleta Piese (Selecteaza pentru a desena)")
        palette_layout = QGridLayout()
        
        pieces_w = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP']
        pieces_b = ['bK', 'bQ', 'bR', 'bB', 'bN', 'bP']
        
        for i, p in enumerate(pieces_w):
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join(self.images_dir, f"{p}.png")))
            btn.setIconSize(QSize(40, 40))
            btn.clicked.connect(lambda checked, piece=p: self.set_stamp(piece))
            palette_layout.addWidget(btn, 0, i)
            
        for i, p in enumerate(pieces_b):
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join(self.images_dir, f"{p}.png")))
            btn.setIconSize(QSize(40, 40))
            btn.clicked.connect(lambda checked, piece=p: self.set_stamp(piece))
            palette_layout.addWidget(btn, 1, i)
            
        # Guma de sters
        btn_eraser = QPushButton("🧹 Guma de sters")
        btn_eraser.clicked.connect(lambda: self.set_stamp("--"))
        palette_layout.addWidget(btn_eraser, 2, 0, 1, 6)
        
        palette_group.setLayout(palette_layout)
        right_layout.addWidget(palette_group)
        
        # 3. Setari: Cine muta?
        turn_group = QGroupBox("Cine muta?")
        turn_layout = QHBoxLayout()
        self.radio_white = QRadioButton("Alb")
        self.radio_black = QRadioButton("Negru")
        self.radio_white.setChecked(True)
        turn_layout.addWidget(self.radio_white)
        turn_layout.addWidget(self.radio_black)
        turn_group.setLayout(turn_layout)
        right_layout.addWidget(turn_group)
        
        # 4. Setari: Drepturi de Rocada
        castle_group = QGroupBox("Drepturi de Rocada")
        castle_layout = QGridLayout()
        self.cb_wK = QCheckBox("Alb - Scurta (K)")
        self.cb_wQ = QCheckBox("Alb - Lunga (Q)")
        self.cb_bK = QCheckBox("Negru - Scurta (k)")
        self.cb_bQ = QCheckBox("Negru - Lunga (q)")
        
        # Le bifam pe toate implicit
        for cb in [self.cb_wK, self.cb_wQ, self.cb_bK, self.cb_bQ]:
            cb.setChecked(False)
            
        castle_layout.addWidget(self.cb_wK, 0, 0)
        castle_layout.addWidget(self.cb_wQ, 0, 1)
        castle_layout.addWidget(self.cb_bK, 1, 0)
        castle_layout.addWidget(self.cb_bQ, 1, 1)
        castle_group.setLayout(castle_layout)
        right_layout.addWidget(castle_group)
        
        # 5. Salvare / Anulare
        right_layout.addStretch()
        action_layout = QHBoxLayout()
        btn_apply = QPushButton("Salvez Pozitia (Generare FEN)")
        btn_apply.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        btn_apply.clicked.connect(self.validate_and_save)
        
        btn_cancel = QPushButton("Anuleaza")
        btn_cancel.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; height: 40px;")
        btn_cancel.clicked.connect(self.reject)
        
        action_layout.addWidget(btn_apply)
        action_layout.addWidget(btn_cancel)
        right_layout.addLayout(action_layout)
        
        main_layout.addWidget(right_panel)

    # --- LOGICA DE DESENARE ---
    def set_stamp(self, piece_code):
        """Seteaza piesa pe care vrem sa o punem pe tabla"""
        self.current_stamp = piece_code
        if piece_code == "--":
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def apply_stamp(self, r, c):
        """Pune piesa pe patratelul pe care am dat click"""
        self.board[r][c] = self.current_stamp
        self.update_square_visual(r, c)

    def update_square_visual(self, r, c):
        """Actualizeaza imaginea de pe ecran"""
        piece = self.board[r][c]
        if piece == "--":
            self.squares[r][c].setPixmap(QPixmap()) # Golim
        else:
            pixmap = QPixmap(os.path.join(self.images_dir, f"{piece}.png"))
            # Scalam frumos piesa la patratelul de 60x60
            self.squares[r][c].setPixmap(pixmap.scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def clear_board(self):
        self.board = [["--" for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                self.update_square_visual(r, c)
                
    def load_starting_position(self):
        start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.load_fen(start_fen)

    def load_fen(self, fen):
        """Incarca un FEN in editor pentru a-l modifica"""
        self.clear_board()
        parts = fen.split(" ")
        ranks = parts[0].split("/")
        
        # Mapam literele FEN in codurile noastre (ex: 'p' -> 'bP', 'K' -> 'wK')
        fen_to_piece = {
            'P': 'wP', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bP', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
        }
        
        for r in range(8):
            c = 0
            for char in ranks[r]:
                if char.isdigit():
                    c += int(char)
                else:
                    self.board[r][c] = fen_to_piece[char]
                    self.update_square_visual(r, c)
                    c += 1
                    
        # Setari extra
        if len(parts) > 1:
            if parts[1] == 'b':
                self.radio_black.setChecked(True)
            else:
                self.radio_white.setChecked(True)
                
        if len(parts) > 2:
            castling = parts[2]
            self.cb_wK.setChecked('K' in castling)
            self.cb_wQ.setChecked('Q' in castling)
            self.cb_bK.setChecked('k' in castling)
            self.cb_bQ.setChecked('q' in castling)

    # --- GENERARE REZULTAT (FEN) ---
    def get_generated_fen(self):
        """Converteste tabla desenata inapoi intr-un string FEN valid"""
        piece_to_fen = {
            'wP': 'P', 'wN': 'N', 'wB': 'B', 'wR': 'R', 'wQ': 'Q', 'wK': 'K',
            'bP': 'p', 'bN': 'n', 'bB': 'b', 'bR': 'r', 'bQ': 'q', 'bK': 'k'
        }
        
        fen_board = ""
        for r in range(8):
            empty_count = 0
            for c in range(8):
                piece = self.board[r][c]
                if piece == "--":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_board += str(empty_count)
                        empty_count = 0
                    fen_board += piece_to_fen[piece]
            if empty_count > 0:
                fen_board += str(empty_count)
            if r < 7:
                fen_board += "/"
                
        # Cine muta
        turn = "w" if self.radio_white.isChecked() else "b"
        
        # Drepturi de rocada
        castling = ""
        if self.cb_wK.isChecked(): castling += "K"
        if self.cb_wQ.isChecked(): castling += "Q"
        if self.cb_bK.isChecked(): castling += "k"
        if self.cb_bQ.isChecked(): castling += "q"
        if not castling: castling = "-"
        
        # En passant si move counters (simplificat)
        en_passant = "-"
        halfmove = "0"
        fullmove = "1"
        
        return f"{fen_board} {turn} {castling} {en_passant} {halfmove} {fullmove}"
    
    def validate_and_save(self):
        """Verifica daca pozitia desenata e legal posibila inainte de a o trimite la motor"""
        import chess
        from PyQt6.QtWidgets import QMessageBox
        
        test_fen = self.get_generated_fen()
        
        try:
            board = chess.Board(test_fen)
            
            # Verificam daca pozitia e legal posibila
            if not board.is_valid():
                # Daca nu e valida, extragem motivele exacte
                status = board.status()
                erori = []
                if status & chess.STATUS_NO_WHITE_KING: erori.append("Lipseste regele alb.")
                if status & chess.STATUS_NO_BLACK_KING: erori.append("Lipseste regele negru.")
                if status & chess.STATUS_TOO_MANY_KINGS: erori.append("Exista prea multi regi pe tabla.")
                if status & chess.STATUS_PAWNS_ON_BACKRANK: erori.append("Ai pioni pe prima sau ultima linie.")
                if status & chess.STATUS_TOO_MANY_BLACK_PIECES or status & chess.STATUS_TOO_MANY_WHITE_PIECES: 
                    erori.append("Prea multe piese de o singura culoare.")
                if status & chess.STATUS_OPPOSITE_CHECK: erori.append("Ambii regi sunt in sah simultan.")
                
                mesaj = "Pozitia este ILEGALA si ar bloca motorul de analiza!\n\nMotive:\n- " + "\n- ".join(erori)
                if not erori:
                    mesaj = "Pozitie imposibila conform regulilor de sah (ex: pion promovat dar pus gresit)."
                    
                QMessageBox.warning(self, "Pozitie Invalida", mesaj)
                return # Oprim executia, nu lasam fereastra sa se inchida!
                
            # Daca a trecut de toate filtrele, abia acum ii dam voie sa inchida si sa salveze
            self.accept()
            
        except ValueError:
            QMessageBox.critical(self, "Eroare Fatala", "Structura FEN este complet corupta.")