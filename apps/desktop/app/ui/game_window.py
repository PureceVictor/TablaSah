# app/ui/game_window.py
import os
from app.core.engine_worker import EngineWorker
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QSplitter, QTabWidget, QToolBar, QTextBrowser,
                             QFileDialog, QInputDialog, QMessageBox, QPushButton)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QFont
from PyQt6.QtCore import Qt

from app.core.game_manager import GameState
from app.ui.board_widget import BoardWidget
from app.ui.engine_settings_dialog import EngineSettingsDialog

class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Partida - AI Chess Assistant")
        self.setMinimumSize(1100, 700)
        
        # Ca sa nu ne pierdem ferestrele in memorie cand dam "New Game"
        self.child_windows = []
        self.engine_threads = 2
        self.engine_hash = 2048
        self.engine_num_lines = 2
        self.engine_worker = None
        
        self.setup_menus_and_toolbars()
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)
        
        self.game_state = GameState()
        self.board_widget = BoardWidget(self.game_state, on_move_callback=self.update_notation)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.tabs = QTabWidget()
        
        # TAB 1: Notatie
        self.tab_notation = QTextBrowser() 
        self.tab_notation.setReadOnly(True)
        self.tab_notation.setStyleSheet("font-size: 14px; padding: 5px;")
        self.tab_notation.setOpenLinks(False) 
        self.tab_notation.anchorClicked.connect(self.on_notation_clicked)
        self.tabs.addTab(self.tab_notation, "Notation")
        
        # TAB 2: Training (Doar ultima mutare)
        self.tab_training = QTextBrowser()
        self.tab_training.setReadOnly(True)
        self.tab_training.setStyleSheet("font-size: 14px; padding: 5px;")
        self.tabs.addTab(self.tab_training, "Training")
        
        # TAB 3: Baza de date deschideri
        self.tab_book = QLabel("Opening Book\n(Statistici mutari din baza de date)")
        self.tab_book.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tab_book.setStyleSheet("background-color: #e9ecef;")
        self.tabs.addTab(self.tab_book, "Book")
        
        # --- CONTAINERUL STOCKFISH ---
        self.engine_container = QWidget()
        engine_layout = QVBoxLayout(self.engine_container)
        engine_layout.setContentsMargins(0, 0, 0, 0)
        
        # Bara superioara de control (+ / -)
        controls_layout = QHBoxLayout()
        self.lines_label = QLabel(f"Linii: {self.engine_num_lines}")
        self.lines_label.setStyleSheet("color: #333; font-weight: bold; padding: 2px;")
        
        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(25, 25)
        btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minus.clicked.connect(self.action_decrease_lines)
        
        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(25, 25)
        btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plus.clicked.connect(self.action_increase_lines)
        
        controls_layout.addWidget(self.lines_label)
        controls_layout.addWidget(btn_minus)
        controls_layout.addWidget(btn_plus)
        controls_layout.addStretch() # Impinge butoanele la stanga
        
        # Panoul de text (Consola verde)
        self.engine_panel = QTextEdit()
        self.engine_panel.setReadOnly(True)
        self.engine_panel.setStyleSheet("background-color: #1e1e1e; color: #4CAF50; font-family: Consolas; font-size: 13px;")
        self.engine_panel.setText("Stockfish 16.1\n[Asteapta motorul...]")
        
        engine_layout.addLayout(controls_layout)
        engine_layout.addWidget(self.engine_panel)
        
        self.engine_container.hide() # Ascundem intregul container initial
        
        # Panoul AI Coach
        self.ai_chat_area = QTextEdit()
        self.ai_chat_area.setReadOnly(True)
        self.ai_chat_area.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6; font-family: Consolas;")
        self.ai_chat_area.setPlaceholderText("AI Coach: Pozitie echilibrata. Astept mutarea...")
        
        right_splitter.addWidget(self.tabs)
        right_splitter.addWidget(self.engine_container) # Adaugam Stockfish la mijloc
        right_splitter.addWidget(self.ai_chat_area)
        right_splitter.setSizes([500, 200, 200]) # Raportul de marimi cand sunt toate deschise
        
        main_splitter.addWidget(self.board_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([800, 300])

        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.go_back)
        
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.go_forward)

    def setup_menus_and_toolbars(self):
        menubar = self.menuBar()
        
        game_menu = menubar.addMenu("&Game")
        new_action = QAction("New Game", self)
        new_action.triggered.connect(self.action_new_game)
        
        save_action = QAction("Save PGN", self)
        save_action.triggered.connect(self.action_save_pgn)
        
        game_menu.addAction(new_action)
        game_menu.addAction(save_action)
        
        pos_menu = menubar.addMenu("&Position")
        edit_pos_action = QAction("Edit Position (FEN)", self)
        edit_pos_action.triggered.connect(self.action_edit_position)
        pos_menu.addAction(edit_pos_action)
        
        engine_menu = menubar.addMenu("&Engine")
        add_bot_action = QAction("Toggle Stockfish Lines", self)
        add_bot_action.triggered.connect(self.action_toggle_engine)
        engine_menu.addAction(add_bot_action)
        
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        toolbar.addSeparator()
        toolbar.addAction(edit_pos_action)
        toolbar.addAction(add_bot_action)
        engine_settings_action = QAction("Engine Settings...", self)
        engine_settings_action.triggered.connect(self.action_engine_settings)
        engine_menu.addAction(engine_settings_action)

    # --- ACTIUNILE BUTOANELOR ---
    def action_new_game(self):
        new_window = GameWindow()
        self.child_windows.append(new_window)
        new_window.show()

    def action_save_pgn(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Salveaza Partida", "", "PGN Files (*.pgn)")
        if file_path:
            clean_pgn = self.game_state.get_clean_pgn()
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(clean_pgn)
                QMessageBox.information(self, "Succes", "Partida a fost salvata cu succes!")
            except Exception as e:
                QMessageBox.critical(self, "Eroare", f"Nu s-a putut salva fisierul:\n{e}")

    def action_edit_position(self):
        fen, ok = QInputDialog.getText(self, "Seteaza Pozitia", "Introdu codul FEN:")
        if ok and fen:
            self.game_state.load_fen(fen)
            # Aici vom redesena tabla dupa ce facem functia in backend
            # self.board_widget.draw_board_and_pieces()

    def action_toggle_engine(self):
        """Arata sau ascunde panoul verde de Stockfish"""
        if self.engine_container.isHidden():      # <-- Modificat
            self.engine_container.show()          # <-- Modificat
            
            if self.engine_worker is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                engine_path = os.path.join(current_dir, "..", "engine", "stockfish18.exe")
                
                self.engine_worker = EngineWorker(engine_path, self.engine_threads, self.engine_hash)
                self.engine_worker.set_lines(self.engine_num_lines) # Ii trimitem nr de linii initial
                self.engine_worker.update_signal.connect(self.update_engine_ui)
                self.engine_worker.start()
                
            uci_path = self.game_state.get_current_uci_path()
            self.engine_worker.update_position(uci_path)
        else:
            self.engine_container.hide()          # <-- Modificat
            if self.engine_worker is not None:
                self.engine_worker.stop()
                self.engine_worker = None


    def action_engine_settings(self):
        dialog = EngineSettingsDialog(self.engine_threads, self.engine_hash, self)
        if dialog.exec():
            # Extragem noile valori
            self.engine_threads, self.engine_hash = dialog.get_values()
            
            # Daca Stockfish ruleaza deja in spate, trebuie sa il oprim si sa il pornim cu noile setari
            if self.engine_worker is not None and not self.engine_panel.isHidden():
                self.engine_worker.stop()
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                engine_path = os.path.join(current_dir, "..", "engine", "stockfish18.exe")
                
                self.engine_worker = EngineWorker(engine_path, self.engine_threads, self.engine_hash)
                self.engine_worker.update_signal.connect(self.update_engine_ui)
                self.engine_worker.start()
                
                uci_path = self.game_state.get_current_uci_path()
                self.engine_worker.update_position(uci_path)
    

    def update_engine_ui(self, text):
        """Primeste datele de la Thread si actualizeaza casuta verde"""
        self.engine_panel.setText(text)

    # --- ACTUALIZARE UI (Notatie si Training) ---
    def update_notation(self):
        # Update Notatie HTML
        notation_text = self.game_state.getNotationText()
        self.tab_notation.setHtml(notation_text)
        
        # --- UPDATE TAB TRAINING (La fel ca design-ul de notatie) ---
        path = self.game_state.get_current_uci_path()
        half_moves = len(path)
        
        if half_moves > 0 and self.game_state.current_node.move is not None:
            move_num = (half_moves + 1) // 2
            last_move_str = self.game_state.current_node.move.getChessNotation()
            
            # Construim HTML-ul fix ca la panoul principal
            html = "<style>body { font-family: sans-serif; }</style>"
            
            if half_moves % 2 != 0:
                # A fost mutarea albului
                html += f"<b>{move_num}.</b> {last_move_str}"
            else:
                # A fost mutarea negrului
                html += f"<i>{move_num}...</i> {last_move_str}"
                
            self.tab_training.setHtml(html)
        else:
            self.tab_training.setHtml("<i>Asteapta prima mutare...</i>")

    def on_notation_clicked(self, url):
        url_str = url.toString()
        if url_str.startswith("move:"):
            node_id = url_str[5:]
        elif url_str.startswith("file:///"): 
            node_id = url_str.split("/")[-1]
        else:
            node_id = url_str 
            
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

    def action_decrease_lines(self):
        if self.engine_num_lines > 1:
            self.engine_num_lines -= 1
            self.update_engine_lines_ui()

    def action_increase_lines(self):
        if self.engine_num_lines < 6:
            self.engine_num_lines += 1
            self.update_engine_lines_ui()

    def update_engine_lines_ui(self):
        self.lines_label.setText(f"Linii: {self.engine_num_lines}")
        if self.engine_worker is not None:
            self.engine_worker.set_lines(self.engine_num_lines)