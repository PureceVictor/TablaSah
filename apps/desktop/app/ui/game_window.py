# app/ui/game_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QSplitter, QTabWidget, QToolBar, QTextBrowser)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt

from app.core.game_manager import GameState
from app.ui.board_widget import BoardWidget

class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Partida - AI Chess Assistant")
        self.setMinimumSize(1100, 700)
        
        # 1. BARA DE MENIU SI UNELTE (TOP BAR)
        self.setup_menus_and_toolbars()
        
        # 2. SPLITTER PRINCIPAL (Stanga vs Dreapta)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # --- ZONA STANGA: Motorul de Sah si Tabla Grafica ---
        self.game_state = GameState()
        self.board_widget = BoardWidget(self.game_state, on_move_callback=self.update_notation)
        
        # --- ZONA DREAPTA: Splitter Vertical (Tab-uri sus, AI Chat jos) ---
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 2.A. Tab-urile pentru notatii si antrenament
        self.tabs = QTabWidget()
        
        # Tab 1: Notatia clasica
        self.tab_notation = QTextBrowser() 
        self.tab_notation.setReadOnly(True)
        self.tab_notation.setStyleSheet("font-size: 14px; padding: 5px;")
        self.tab_notation.setOpenLinks(False) 
        self.tab_notation.anchorClicked.connect(self.on_notation_clicked)
        self.tabs.addTab(self.tab_notation, "Notation")
        
        # Tab 2: Modul Training
        self.tab_training = QLabel("Training Mode\n(Doar ultima mutare vizibila)")
        self.tab_training.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tab_training.setStyleSheet("background-color: #e9ecef;")
        self.tabs.addTab(self.tab_training, "Training")
        
        # Tab 3: Baza de date deschideri
        self.tab_book = QLabel("Opening Book\n(Statistici mutari din baza de date)")
        self.tab_book.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tab_book.setStyleSheet("background-color: #e9ecef;")
        self.tabs.addTab(self.tab_book, "Book")
        
        # 2.B. Panoul AI Coach (Jos)
        self.ai_chat_area = QTextEdit()
        self.ai_chat_area.setReadOnly(True)
        self.ai_chat_area.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6; font-family: Consolas;")
        self.ai_chat_area.setPlaceholderText("AI Coach: Pozitie echilibrata. Astept mutarea...")
        
        right_splitter.addWidget(self.tabs)
        right_splitter.addWidget(self.ai_chat_area)
        right_splitter.setSizes([700, 300])
        
        # --- ASAMBLARE FINALA ---
        main_splitter.addWidget(self.board_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([800, 300])

        # --- SCURTATURI TASTATURA ---
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.go_back)
        
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.go_forward)

    def setup_menus_and_toolbars(self):
        menubar = self.menuBar()
        game_menu = menubar.addMenu("&Game")
        new_action = QAction("New Game", self)
        save_action = QAction("Save PGN", self)
        game_menu.addAction(new_action)
        game_menu.addAction(save_action)
        
        pos_menu = menubar.addMenu("&Position")
        edit_pos_action = QAction("Edit Position (FEN)", self)
        pos_menu.addAction(edit_pos_action)
        
        engine_menu = menubar.addMenu("&Engine")
        add_bot_action = QAction("Add Bot (Stockfish)", self)
        engine_menu.addAction(add_bot_action)
        
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        toolbar.addSeparator()
        toolbar.addAction(edit_pos_action)
        toolbar.addAction(add_bot_action)

    def update_notation(self):
        notation_text = self.game_state.getNotationText()
        self.tab_notation.setHtml(notation_text)

    def on_notation_clicked(self, url):
        url_str = url.toString()
        print(f"[DEBUG UI] Click interceptat pe: {url_str}")
        
        if url_str.startswith("move:"):
            node_id = url_str[5:] 
            self.game_state.play_to_node(node_id)
            
            self.board_widget.valid_moves = self.game_state.allValidMoves()
            self.board_widget.draw_board_and_pieces()
            self.update_notation()

    def go_back(self):
        self.game_state.undoMove()
        self.board_widget.valid_moves = self.game_state.allValidMoves()
        self.board_widget.draw_board_and_pieces()
        self.update_notation()

    def go_forward(self):
        self.game_state.redoMove(0)
        self.board_widget.valid_moves = self.game_state.allValidMoves()
        self.board_widget.draw_board_and_pieces()
        self.update_notation()