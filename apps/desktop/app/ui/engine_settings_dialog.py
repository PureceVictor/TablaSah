# app/ui/engine_settings_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton
import os

class EngineSettingsDialog(QDialog):
    def __init__(self, current_threads, current_hash, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setari Stockfish")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        
        # Setare Threads
        threads_layout = QHBoxLayout()
        threads_label = QLabel("Threads (Core-uri logice):")
        self.threads_spin = QSpinBox()
        # Maximizam la numarul de core-uri vazute de Windows (la tine va fi probabil 32)
        self.threads_spin.setRange(1, os.cpu_count() or 4) 
        self.threads_spin.setValue(current_threads)
        threads_layout.addWidget(threads_label)
        threads_layout.addWidget(self.threads_spin)
        
        # Setare Hash (RAM)
        hash_layout = QHBoxLayout()
        hash_label = QLabel("Hash (RAM in MB):")
        self.hash_spin = QSpinBox()
        # Permitem intre 16 MB si 16384 MB (16 GB)
        self.hash_spin.setRange(16, 16384) 
        self.hash_spin.setSingleStep(256) # Creste din 256 in 256 MB
        self.hash_spin.setValue(current_hash)
        hash_layout.addWidget(hash_label)
        hash_layout.addWidget(self.hash_spin)
        
        # Butoane Salvare/Anulare
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Salveaza")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Anuleaza")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(threads_layout)
        layout.addLayout(hash_layout)
        layout.addLayout(btn_layout)
        
    def get_values(self):
        return self.threads_spin.value(), self.hash_spin.value()