# app/ui/db_explorer_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from app.ui.game_window import GameWindow

class DatabaseExplorerWindow(QMainWindow):
    def __init__(self, db_name):
        super().__init__()
        self.setWindowTitle(f"Database Explorer - {db_name}")
        self.setMinimumSize(900, 600)
        
        # Salvam instantele partidelor deschise din aceasta baza de date
        self.active_games = []
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # --- ZONA DE SUS: Bara de Cautare ---
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Cauta jucator (ex: Kasparov, Carlsen)...")
        self.search_bar.setFixedHeight(35)
        
        btn_search = QPushButton("Cauta")
        btn_search.setFixedHeight(35)
        btn_search.setFixedWidth(100)
        
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(btn_search)
        
        # --- ZONA DE JOS: Tabelul cu Partide ---
        self.games_table = QTableWidget()
        self.games_table.setColumnCount(6)
        self.games_table.setHorizontalHeaderLabels(["Alb", "ELO Alb", "Negru", "ELO Negru", "Rezultat", "Data"])
        
        # Facem tabelul sa se intinda frumos pe tot ecranul
        header = self.games_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Numele albului
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Numele negrului
        
        # Setam comportamentul de selectie (sa selecteze toata linia, nu doar o celula)
        self.games_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.games_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        
        # Conectam dublu-click-ul pe un rand pentru a deschide partida
        self.games_table.itemDoubleClicked.connect(self.open_selected_game)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.games_table)
        
        # Incarcam niste date de test (Mock Data)
        self.load_mock_data()

    def load_mock_data(self):
        """Functie temporara pentru a popula tabelul pana cand vom implementa parser-ul PGN"""
        mock_games = [
            ("Kasparov, Garry", "2812", "Topalov, Veselin", "2700", "1-0", "1999.01.20"),
            ("Carlsen, Magnus", "2882", "Caruana, Fabiano", "2832", "1/2-1/2", "2018.11.09"),
            ("Fischer, Bobby", "2780", "Spassky, Boris", "2660", "1-0", "1972.07.23")
        ]
        
        self.games_table.setRowCount(len(mock_games))
        for row_idx, game_data in enumerate(mock_games):
            for col_idx, item_text in enumerate(game_data):
                self.games_table.setItem(row_idx, col_idx, QTableWidgetItem(item_text))

    def open_selected_game(self, item):
        """Se apeleaza la dublu-click pe un rand si deschide GameWindow"""
        row = item.row()
        white_player = self.games_table.item(row, 0).text()
        black_player = self.games_table.item(row, 2).text()
        
        # Deschidem fereastra de joc
        game = GameWindow()
        game.setWindowTitle(f"{white_player} vs {black_player} - Analiza")
        self.active_games.append(game)
        game.show()