import pygame as p
import os
from app.core.game_manager import GameState, Move


WIDTH = HEIGHT =  512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ["wP","wR","wN","wB","wQ","wK","bP","bR","bK","bB","bQ","bN"]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir,"..","assets","pieces")
    for piece in pieces:
        path = os.path.join(assets_dir, piece + ".png")
        IMAGES[piece] = p.transform.scale(p.image.load(path), (SQ_SIZE,SQ_SIZE))

"""

Functile care sunt responsabile de toate elementele grafice de pe tabla la un moment dat

"""

def drawGameState(screen, gameState):
    drawBoard(screen) #afiseaza campurile de pe tabla
    #se pot adauga sageti, highlighturi, etc
    drawPieces(screen, gameState.board)

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("grey")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gameState = GameState()
    validMoves = gameState.allValidMoves()
    madeMove = False
    load_images()
    running = True
    squareSelected = () #campurile selectate de utilizator
    playerClicks = [] #campul initial si final, practic o mutare
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            #Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                col = location[0]//SQ_SIZE #campul reprezentat pe rand/coloana
                row = location[1]//SQ_SIZE

                if squareSelected == (row, col):
                    squareSelected = ()
                    playerClicks = []
                else:
                    squareSelected = (row, col)
                    playerClicks.append(squareSelected)
                if len(playerClicks) == 2:
                    move = Move(playerClicks[0], playerClicks[1], gameState.board)
                    print(move.getChessNotation())
                    #Validam mutarea
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            gameState.makeMove(validMoves[i])
                            madeMove = True

                    squareSelected = ()
                    playerClicks = []

            #Keyboard handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gameState.undoMove()
                    madeMove = True

        if madeMove:
            validMoves = gameState.allValidMoves()
            madeMove = False
        drawGameState(screen, gameState)
        clock.tick(MAX_FPS)
        p.display.flip()

main()