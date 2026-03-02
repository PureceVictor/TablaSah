# app/ui/board_widget.py
import os
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt6.QtGui import QColor, QPixmap, QBrush, QPen
from PyQt6.QtCore import Qt
from app.core.game_manager import Move

class BoardWidget(QGraphicsView):
    def __init__(self, game_state, on_move_callback=None):
        super().__init__()
        # Motorul de sah asignat strict acestei table
        self.game_state = game_state
        self.on_move_callback = on_move_callback
        
        # Initializam "Panza" (Scene)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Dimensiunea logica a unui patrat. Nu conteaza cat de mare e fereastra,
        # PyQt va scala automat totul pe baza acestui patrat de 80x80 pixeli.
        self.sq_size = 80
        self.scene.setSceneRect(0, 0, self.sq_size * 8, self.sq_size * 8)
        
        self.images = {}
        self.load_images()
        
        # Variabile pentru logica de interactiune
        self.valid_moves = self.game_state.allValidMoves()
        self.square_selected = () # (rand, coloana)
        self.player_clicks = []   # [(r1, c1), (r2, c2)]
        
        # Fara margini urate in jurul tablei
        self.setStyleSheet("border: none;")
        
        # Desenam tabla pentru prima data
        self.draw_board_and_pieces()

    def resizeEvent(self, event):
        """Magia de scalare automata: cand redimensionezi fereastra, tabla se adapteaza perfect"""
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def load_images(self):
        """Incarca imaginile din folderul de assets intr-un dictionar de QPixmaps"""
        pieces = ["wP","wR","wN","wB","wQ","wK","bP","bR","bK","bB","bQ","bN"]
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "..", "assets", "pieces")
        
        for piece in pieces:
            path = os.path.join(assets_dir, f"{piece}.png")
            if os.path.exists(path):
                # Scalare fina a imaginilor PNG
                pixmap = QPixmap(path).scaled(self.sq_size, self.sq_size, 
                                              Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                self.images[piece] = pixmap
            else:
                print(f"ATENTIE: Nu s-a gasit imaginea: {path}")

    def draw_board_and_pieces(self):
        """Metoda de redare completa a tablei (sterge tot si redeseneaza)"""
        self.scene.clear()
        
        # Paleta de culori Chess.com
        light_color = QColor(235, 236, 208)
        dark_color = QColor(115, 149, 82)
        highlight_color = QColor(245, 246, 130, 200)

        for r in range(8):
            for c in range(8):
                # 1. Desenare patrat de baza
                color = light_color if (r + c) % 2 == 0 else dark_color
                if self.square_selected == (r, c):
                    color = highlight_color
                    
                rect = QGraphicsRectItem(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size)
                rect.setBrush(QBrush(color))
                rect.setPen(QPen(Qt.PenStyle.NoPen))
                self.scene.addItem(rect)
                
                # 2. Desenare Piese
                piece = self.game_state.board[r][c]
                if piece != "--" and piece in self.images:
                    pixmap_item = QGraphicsPixmapItem(self.images[piece])
                    pixmap_item.setPos(c * self.sq_size, r * self.sq_size)
                    self.scene.addItem(pixmap_item)
                    
        # 3. Desenare Hint-uri (Bulinele pentru mutarile valide)
        if self.square_selected != ():
            r, c = self.square_selected
            if self.game_state.board[r][c][0] == ('w' if self.game_state.whiteToMove else 'b'):
                for move in self.valid_moves:
                    if move.startRow == r and move.startCol == c:
                        radius = self.sq_size // 6
                        center_x = move.endCol * self.sq_size + self.sq_size // 2 - radius
                        center_y = move.endRow * self.sq_size + self.sq_size // 2 - radius
                        
                        circle = QGraphicsEllipseItem(center_x, center_y, radius*2, radius*2)
                        circle.setBrush(QBrush(QColor(0, 0, 0, 50)))
                        circle.setPen(QPen(Qt.PenStyle.NoPen))
                        self.scene.addItem(circle)

    def mousePressEvent(self, event):
        """Inlocuieste event loop-ul din Pygame. Este chemat automat de PyQt la fiecare click."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Mapam coordonatele click-ului din ecran la coordonatele Scenei (80x80)
            scene_pos = self.mapToScene(event.pos())
            col = int(scene_pos.x() // self.sq_size)
            row = int(scene_pos.y() // self.sq_size)
            
            # Ne asiguram ca userul nu da click in afara matricii 8x8
            if 0 <= row <= 7 and 0 <= col <= 7:
                if self.square_selected == (row, col):
                    self.square_selected = ()
                    self.player_clicks = []
                else:
                    self.square_selected = (row, col)
                    self.player_clicks.append(self.square_selected)
                    
                if len(self.player_clicks) == 2:
                    move = Move(self.player_clicks[0], self.player_clicks[1], self.game_state.board)
                    
                    made_move = False
                    for valid_move in self.valid_moves:
                        if move == valid_move:
                            self.game_state.makeMove(valid_move)
                            made_move = True
                            self.square_selected = ()
                            self.player_clicks = []
                            self.valid_moves = self.game_state.allValidMoves()
                            
                            # 2. Anuntam fereastra ca s-a facut o mutare cu succes!
                            if self.on_move_callback:
                                self.on_move_callback()
                                
                            break
                    if not made_move:
                        # Daca a dat click aiurea, mutam selectia pe noua piesa
                        self.player_clicks = [self.square_selected]
                        
                # Cerem redesenarea tablei cu noua stare
                self.draw_board_and_pieces()