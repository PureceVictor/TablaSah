# app/ui/db_explorer_window.py
import os
import sqlite3
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QProgressBar, QPushButton, QStackedWidget, QMessageBox, QWidget, QLineEdit)
from PyQt6.QtCore import Qt
from app.core.db_builder import DatabaseBuilderWorker

class DatabaseExplorerWindow(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Database Explorer - {os.path.basename(file_path)}")
        self.setMinimumSize(1000, 600)
        self.file_path = file_path
        self.db_path = file_path + ".db" # Aici va cauta booster-ul nostru SQLite
        self.selected_offset = None
        self.loaded_rows = 0
        self.batch_size = 1000
        self.sort_column = "date" # Sortam implicit dupa data
        self.sort_order = "DESC"  # Cele mai noi primele
        self.search_query = ""  
        
        # QStackedWidget ne permite sa trecem de la 'Loading' la 'Tabel' fara sa deschidem alte ferestre
        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        
        self.setup_loading_ui()
        self.setup_table_ui()
        
        # LOGICA DE RUTARE: Avem deja indexul construit?
        if os.path.exists(self.db_path):
            self.stack.setCurrentWidget(self.page_table)
            self.load_data_from_db()
        else:
            self.stack.setCurrentWidget(self.page_loading)
            self.start_indexing()
            
    def setup_loading_ui(self):
        """Construieste ecranul de incarcare cu Bara de Progres"""
        self.page_loading = QWidget()
        layout = QVBoxLayout(self.page_loading)
        
        self.lbl_status = QLabel("Se construieste indexul bazei de date...")
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #ccc; border-radius: 5px; text-align: center; font-weight: bold; } QProgressBar::chunk { background-color: #4CAF50; width: 20px; }")
        
        self.btn_cancel = QPushButton("Anuleaza Indexarea")
        self.btn_cancel.setFixedWidth(200)
        self.btn_cancel.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.btn_cancel.clicked.connect(self.cancel_indexing)
        
        layout.addStretch()
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        
        self.stack.addWidget(self.page_loading)
        
    def setup_table_ui(self):
        """Construieste ecranul cu Tabelul de meciuri"""
        self.page_table = QWidget()
        layout = QVBoxLayout(self.page_table)
        
        self.lbl_info = QLabel("Se incarca...")
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 14px; color: #2196F3;")
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Alb", "ELO Alb", "Negru", "ELO Negru", "Rezultat", "Data", "Eveniment"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # --- FIX CULORI (Text negru, fundal alb/gri deschis alternat) ---
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { font-size: 13px; color: #000000; background-color: #ffffff; alternate-background-color: #f2f2f2; } 
            QHeaderView::section { font-weight: bold; background-color: #e0e0e0; color: #000000; }
        """)
        
        self.table.itemDoubleClicked.connect(self.game_selected)
        
        # --- CONECTAM BARA DE SCROLL PENTRU INCARCARE INFINITA ---
        self.table.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cauta jucator (ex: Carlsen, Kasparov)...")
        self.search_input.setStyleSheet("font-size: 14px; padding: 5px; border: 1px solid #ccc; border-radius: 4px;")
        self.search_input.returnPressed.connect(self.on_search_clicked) # Cauta cand apesi Enter
        
        btn_search = QPushButton("🔍 Cauta")
        btn_search.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 5px 15px;")
        btn_search.clicked.connect(self.on_search_clicked)
        
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.on_reset_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_reset)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.table)
        self.stack.addWidget(self.page_table)
        
    def start_indexing(self):
        """Porneste Muncitorul in fundal"""
        self.worker = DatabaseBuilderWorker(self.file_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.indexing_finished)
        self.worker.error.connect(self.indexing_error)
        self.worker.start() # Aici se lanseaza thread-ul!
        
    def update_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(text)
        
    def indexing_finished(self, db_path):
        """Cand indexarea e gata, schimbam ecranul pe Tabel"""
        self.stack.setCurrentWidget(self.page_table)
        self.load_data_from_db()
        
    def indexing_error(self, err_msg):
        QMessageBox.critical(self, "Eroare Indexare", f"A aparut o eroare critica:\n{err_msg}")
        self.reject()
        
    def cancel_indexing(self):
        """Daca te plictisesti, apesi anuleaza si inchide tot curat"""
        if hasattr(self, 'worker'):
            self.worker.cancel()
        self.reject()
        
    def load_data_from_db(self):
        """Pregateste tabelul si incarca primul pachet de date"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM games")
            total_games = cursor.fetchone()[0]
            self.lbl_info.setText(f"S-au gasit {total_games:,} partide. Fa scroll in jos pentru a incarca mai multe.")
            
            conn.close()
            
            # Resetam tabelul si incarcam primele 1000
            self.table.setRowCount(0)
            self.loaded_rows = 0
            self.load_more_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare Citire DB", f"Nu s-a putut incarca baza de date:\n{e}")

    def on_scroll(self, value):
        """Se declanseaza cand misti de bara de scroll. Daca a ajuns jos, aduce date noi."""
        scrollbar = self.table.verticalScrollBar()
        if value == scrollbar.maximum():
            self.load_more_data()

    def load_more_data(self):
        """Extrage urmatoarele 1000 de meciuri, tinand cont de sortarea actuala"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # --- REPARATIA AICI: Sortare inteligenta ---
            order_clause = f"{self.sort_column} {self.sort_order}"
            
            # Daca sortam dupa ELO, fortam baza de date sa le citeasca drept numere (INTEGER)
            if self.sort_column in ["white_elo", "black_elo"]:
                order_clause = f"CAST({self.sort_column} AS INTEGER) {self.sort_order}"
            
            # --- CONSTRUIM SQL-ul DINAMIC ---
            params = []
            where_clause = ""
            
            # Daca utilizatorul a scris ceva in bara de search
            if self.search_query:
                # Folosim LIKE "Nume%" pentru a forta SQLite sa foloseasca indecsii ultra-rapizi
                where_clause = "WHERE white LIKE ? OR black LIKE ?"
                params.extend([f"{self.search_query}%", f"{self.search_query}%"])
            
            query = f"""
                SELECT white, white_elo, black, black_elo, result, date, event, byte_offset 
                FROM games 
                {where_clause}
                ORDER BY {order_clause} 
                LIMIT {self.batch_size} OFFSET {self.loaded_rows}
            """
            
            # Executam cu parametri (protejeaza si impotriva SQL Injection)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # ... (restul functiei ramane absolut identic de la if not rows: in jos)
            if not rows:
                conn.close()
                return 
                
            current_row_count = self.table.rowCount()
            self.table.setRowCount(current_row_count + len(rows))
            
            for i, row_data in enumerate(rows):
                row_idx = current_row_count + i
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row_data[3])))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(row_data[4])))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row_data[5])))
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(row_data[6])))
                
                self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, row_data[7])
                
            self.loaded_rows += len(rows)
            conn.close()
            
        except Exception as e:
            print(f"Eroare la incarcarea datelor: {e}")

    def on_header_clicked(self, logical_index):
        """Se declanseaza cand dai click pe o coloana din capul tabelului"""
        # Mapam indexul coloanei din UI la numele coloanei din SQLite
        columns_map = {
            0: "white",
            1: "white_elo",
            2: "black",
            3: "black_elo",
            4: "result",
            5: "date",
            6: "event"
        }
        
        clicked_column = columns_map.get(logical_index)
        if not clicked_column:
            return
            
        # Inversam ordinea daca am dat click pe aceeasi coloana, altfel punem ASC
        if self.sort_column == clicked_column:
            self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        else:
            self.sort_column = clicked_column
            self.sort_order = "ASC"
            
        # Curatam tabelul vizual si aducem noile date sortate
        self.table.setRowCount(0)
        self.loaded_rows = 0
        self.load_more_data()
        
        # Actualizam UI-ul ca sa arate utilizatorului directia sortarii
        sort_indicator = " ▲" if self.sort_order == "ASC" else " ▼"
        headers = ["Alb", "ELO Alb", "Negru", "ELO Negru", "Rezultat", "Data", "Eveniment"]
        headers[logical_index] += sort_indicator
        self.table.setHorizontalHeaderLabels(headers)
            
    def game_selected(self, item):
        row = item.row()
        self.selected_offset = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()

    def on_search_clicked(self):
        """Se declanseaza cand apesi Enter sau butonul Cauta"""
        query = self.search_input.text().strip()
        if len(query) < 2:
            return # Nu cautam o singura litera
            
        self.search_query = query
        self.table.setRowCount(0)
        self.loaded_rows = 0
        self.load_more_data()

    def on_reset_search(self):
        """Curata cautarea si aduce tot tabelul la loc"""
        self.search_input.clear()
        self.search_query = ""
        self.table.setRowCount(0)
        self.loaded_rows = 0
        self.load_more_data()