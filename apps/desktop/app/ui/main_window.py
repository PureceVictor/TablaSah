# app/ui/main_window.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QTabWidget, QListWidgetItem
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
        
        # 1. Butonul pentru un singur meci
        btn_import_single = QPushButton("Importa Meci PGN (Partida Singura)")
        btn_import_single.setFixedHeight(50)
        btn_import_single.clicked.connect(self.import_single_pgn)
        
        # 2. Noul Buton pentru Baze de Date
        btn_add_db = QPushButton("Adauga Baza de Date (.PGN)")
        btn_add_db.setFixedHeight(50)
        btn_add_db.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;") 
        btn_add_db.clicked.connect(self.action_add_database_to_list)
        
        btn_settings = QPushButton("Setari AI & Hardware")
        btn_settings.setFixedHeight(50)
        
        left_layout.addWidget(lbl_profile)
        left_layout.addWidget(btn_new_game)
        left_layout.addWidget(btn_import_single)
        left_layout.addWidget(btn_add_db)
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

    def action_add_database_to_list(self):
        """Deschide un dialog ca utilizatorul sa gaseasca fisierul .pgn urias si il adauga in meniul din dreapta"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Adauga Baza de Date PGN", "", "PGN Files (*.pgn)")
        
        if file_path:
            # Extragem doar numele fisierului pentru a arata frumos in UI (ex: Mega2019.pgn)
            file_name = os.path.basename(file_path)
            
            # Cream item-ul pentru lista
            item = QListWidgetItem(f"📚 {file_name}")
            
            # SECRETUL: Ascundem calea completa a fisierului in spatele item-ului!
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            
            # Adaugam in tab-ul din dreapta
            self.db_list.addItem(item)
            
            # Mutam focusul pe tab-ul de baze de date ca sa vada utilizatorul ce s-a intamplat
            self.tabs.setCurrentIndex(1) 

    def open_db_explorer(self, item):
        """Se activeaza la dublu-click pe lista din dreapta si deschide tabelul cu sute de meciuri"""
        # Recuperam calea secreta a fisierului
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Eroare", "Fisierul PGN nu mai exista la calea specificata!")
            return

        explorer = DatabaseExplorerWindow(file_path, self)
        
        # Daca utilizatorul a dat dublu click pe un meci in TABEL (accept()) si avem un offset
        if explorer.exec() and explorer.selected_offset is not None:
            
            game_window = GameWindow()
            self.active_games.append(game_window)
            
            # Incarcam meciul direct de la pozitia indicata (offset)
            headers = PGNParser.load_game_from_offset(file_path, explorer.selected_offset, game_window.game_state)
            
            if headers:
                white = headers.get("White", "Alb")
                black = headers.get("Black", "Negru")
                date = headers.get("Date", "????")
                
                game_window.setWindowTitle(f"{white} vs {black} ({date})")
                game_window.update_notation()
                game_window.board_widget.draw_board_and_pieces()
                
                game_window.show()
            else:
                QMessageBox.critical(self, "Eroare", "Nu s-a putut parsa meciul ales din baza de date!")

    def import_single_pgn(self):
        """Deschide un fisier PGN cu un singur meci si il incarca direct pe tabla"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Deschide Meci PGN", "", "PGN Files (*.pgn)")
        
        if file_path:
            game_window = GameWindow()
            self.active_games.append(game_window)
            
            headers = PGNParser.load_pgn_to_gamestate(file_path, game_window.game_state)
            
            if headers:
                white = headers.get("White", "Alb")
                black = headers.get("Black", "Negru")
                date = headers.get("Date", "????")
                
                game_window.setWindowTitle(f"{white} vs {black} ({date})")
                game_window.update_notation()
                game_window.board_widget.draw_board_and_pieces()
                
                game_window.show()
            else:
                QMessageBox.critical(self, "Eroare", "Nu s-a putut parsa fisierul PGN!")

    def open_database_explorer(self):
        """Deschide Explorer-ul de Baze de Date (Tabelul) pentru fisiere cu mai multe meciuri"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Deschide Baza de Date PGN", "", "PGN Files (*.pgn)")
        
        if file_path:
            explorer = DatabaseExplorerWindow(file_path, self)
            
            # Daca utilizatorul a dat dublu click pe un meci (accept()) si avem un offset
            if explorer.exec() and explorer.selected_offset is not None:
                
                game_window = GameWindow()
                self.active_games.append(game_window)
                
                # Incarcam meciul direct de la pozitia indicata (offset)
                headers = PGNParser.load_game_from_offset(file_path, explorer.selected_offset, game_window.game_state)
                
                if headers:
                    white = headers.get("White", "Alb")
                    black = headers.get("Black", "Negru")
                    date = headers.get("Date", "????")
                    
                    game_window.setWindowTitle(f"{white} vs {black} ({date})")
                    game_window.update_notation()
                    game_window.board_widget.draw_board_and_pieces()
                    
                    game_window.show()
                else:
                    QMessageBox.critical(self, "Eroare", "Nu s-a putut parsa meciul ales din baza de date!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    hub = HubWindow()
    hub.show()
    
    sys.exit(app.exec())