# app/ui/promotion_dialog.py
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt

class PromotionDialog(QDialog):
    def __init__(self, color, images_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Promovare Pion")
        self.setFixedSize(320, 100)
        
        # Daca utilizatorul inchide fereastra din "X", default e Regina
        self.choice = 'Q' 
        
        layout = QHBoxLayout(self)
        
        # Optiunile de promovare
        pieces = ['Q', 'R', 'B', 'N']
        
        for piece in pieces:
            btn = QPushButton()
            btn.setFixedSize(65, 65)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Luam imaginea din dictionarul deja incarcat in BoardWidget
            pixmap = images_dict[f"{color}{piece}"]
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(55, 55))
            
            # Magic trick: lambda captureaza variabila 'piece' pentru fiecare buton in parte
            btn.clicked.connect(lambda checked, p=piece: self.select_piece(p))
            
            layout.addWidget(btn)

    def select_piece(self, piece):
        self.choice = piece
        self.accept() # Aceasta comanda inchide dialogul cu status de "Success"
        
    def get_choice(self):
        return self.choice