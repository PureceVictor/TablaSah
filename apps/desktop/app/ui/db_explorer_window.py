# app/ui/db_explorer_window.py
import os
import sqlite3
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QProgressBar, QPushButton, QStackedWidget, QMessageBox, QWidget)
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
        
        self.lbl_status = QLabel("Se construieste indexul bazei de date (doar prima data)...")
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
        """Extrage urmatoarele 1000 de meciuri din baza de date si le adauga in tabel in 0.01 secunde"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Secretul este clauza OFFSET din SQL, care stie sa sara peste meciurile deja incarcate
            cursor.execute(f"SELECT white, white_elo, black, black_elo, result, date, event, byte_offset FROM games LIMIT {self.batch_size} OFFSET {self.loaded_rows}")
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return # Am ajuns la finalul celor 7 milioane de meciuri
                
            # Adaugam noile randuri la finalul tabelului
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
                
                # Salvam file offset-ul pentru PGN Parser
                self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, row_data[7])
                
            self.loaded_rows += len(rows)
            conn.close()
            
        except Exception as e:
            print(f"Eroare la incarcarea datelor: {e}")
            
    def game_selected(self, item):
        row = item.row()
        self.selected_offset = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()