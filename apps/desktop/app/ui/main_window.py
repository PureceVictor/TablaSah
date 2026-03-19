# app/ui/main_window.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QTabWidget
from PyQt6.QtCore import Qt
from app.ui.game_window import GameWindow
from app.ui.db_explorer_window import DatabaseExplorerWindow
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from app.io.pgn_parser import PGNParser

class HubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chess Assistant - Hub")
        self.setMinimumSize(900, 600)
        
        # LISTA CRITICA: Aici salvam referintele catre partidele deschise
        # Daca nu le salvam, Python le va inchide automat imediat ce functia se termina.
        self.active_games = []
        self.active_explorers = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # --- ZONA STANGA: Meniul de actiuni ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_profile = QLabel("👤 Utilizator: Gavrila Iulian | ELO: ~1200")
        lbl_profile.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        
        btn_new_game = QPushButton("Noua Partida (Joaca / Analizeaza)")
        btn_new_game.setFixedHeight(50)
        btn_new_game.clicked.connect(self.open_new_game)
        
        btn_import = QPushButton("Importa PGN (Baza de date)")
        btn_import.setFixedHeight(50)
        btn_import.clicked.connect(self.import_pgn_file)
        
        btn_settings = QPushButton("Setari AI & Hardware")
        btn_settings.setFixedHeight(50)
        
        left_layout.addWidget(lbl_profile)
        left_layout.addWidget(btn_new_game)
        left_layout.addWidget(btn_import)
        left_layout.addWidget(btn_settings)
        
# --- ZONA DREAPTA: Sistem de Tab-uri ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.tabs = QTabWidget()
        
        # Tab 1: Partide Recente
        self.recent_list = QListWidget()
        self.recent_list.addItems([
            "Analiza mea - Siciliana.pgn",
            "Meci antrenament - 21 Feb.pgn"
        ])
        self.tabs.addTab(self.recent_list, "Partide Recente")
        
        # Tab 2: Baze de Date
        self.db_list = QListWidget()
        self.db_list.addItems([
            "Mega Database 2024 (5.2M partide)",
            "Repertoriu Deschideri Alb",
            "Tacticile lui Kasparov"
        ])
        # Conectam dublu-click-ul la deschiderea explorer-ului
        self.db_list.itemDoubleClicked.connect(self.open_db_explorer)
        self.tabs.addTab(self.db_list, "Baze de Date")
        
        right_layout.addWidget(self.tabs)
        
        # Asamblare Hub
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=2)

    def open_new_game(self):
        """Instantiaza o fereastra complet independenta pentru o noua partida."""
        game = GameWindow()
        self.active_games.append(game)
        game.show()

    def open_db_explorer(self, item):
        """Instantiaza explorer-ul pentru baza de date selectata"""
        db_name = item.text()
        explorer = DatabaseExplorerWindow(db_name)
        self.active_explorers.append(explorer)
        explorer.show()

    def import_pgn_file(self):
        """Deschide un fisier PGN si il incarca intr-o fereastra de joc noua"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Deschide Meci PGN", "", "PGN Files (*.pgn)")
        
        if file_path:
            # 1. Deschidem o fereastra noua de sah
            game_window = GameWindow()
            self.active_games.append(game_window)
            
            # 2. Rulam parser-ul pe GameState-ul acelei ferestre
            headers = PGNParser.load_pgn_to_gamestate(file_path, game_window.game_state)
            
            if headers:
                # 3. Daca a mers, schimbam titlul ferestrei si actualizam UI-ul
                white = headers.get("White", "Alb")
                black = headers.get("Black", "Negru")
                date = headers.get("Date", "????")
                
                game_window.setWindowTitle(f"{white} vs {black} ({date})")
                game_window.update_notation()
                game_window.board_widget.draw_board_and_pieces()
                
                game_window.show()
            else:
                QMessageBox.critical(self, "Eroare", "Nu s-a putut parsa fisierul PGN!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    hub = HubWindow()
    hub.show()
    
    sys.exit(app.exec())