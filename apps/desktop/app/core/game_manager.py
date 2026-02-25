class GameState():
    def __init__(self):
        self.board = [
            ["bR","bN","bB","bQ","bK","bB","bN","bR"],
            ["bP","bP","bP","bP","bP","bP","bP","bP"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["wP","wP","wP","wP","wP","wP","wP","wP"],
            ["wR","wN","wB","wQ","wK","wB","wN","wR"]
        ]
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False

        self.inCheck = False
        self.pins = []
        self.checks = []

    def makeMove(self, move): 
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved #mutarea efectiva


        self.moveLog.append(move) #istoricul de mutari
        self.whiteToMove = not self.whiteToMove

        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)


    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()

            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured

            self.whiteToMove = not self.whiteToMove

            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)



    #Determinam toate mutarile posibile pentru fiecare piesa in particular

    def getPawnMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1 # Directia in sus pentru alb
            startRow = 6
            enemyColor = 'b'
        else:
            moveAmount = 1 # Directia in jos pentru negru
            startRow = 1
            enemyColor = 'w'

        # 1. Mutarea IN FATA (Orizontala pe coloana, vertical pe rand)
        if self.board[row + moveAmount][col] == "--":
            if not piecePinned or pinDirection == (moveAmount, 0): # Doar daca nu e legat sau e legat PE VERTICALA
                moves.append(Move((row, col), (row + moveAmount, col), self.board))
                
                # Mutarea dubla (doar daca prima a fost valida)
                if row == startRow and self.board[row + 2 * moveAmount][col] == "--":
                    moves.append(Move((row, col), (row + 2 * moveAmount, col), self.board))

        # 2. Capturi
        if col - 1 >= 0: # Diagonala stanga
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[row + moveAmount][col - 1][0] == enemyColor:
                    moves.append(Move((row, col), (row + moveAmount, col - 1), self.board))
                    
        if col + 1 <= 7: # Diagonala dreapta
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[row + moveAmount][col + 1][0] == enemyColor:
                    moves.append(Move((row, col), (row + moveAmount, col + 1), self.board))
            

    def getNightMoves(self, row, col, moves):
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        if not piecePinned: # Daca e legat, nu mai face nimic. Daca e liber, genereaza:
            enemyColor = 'b' if self.whiteToMove else 'w'
            mutari = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
            for m in mutari:
                endRow = row + m[0]
                endCol = col + m[1]
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != self.board[row][col][0]: # Patrat gol sau inamic
                        moves.append(Move((row, col), (endRow, endCol), self.board))




    def getBishopMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != 'Q': 
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        
        for d in directions:
            for i in range(1, 8):
                endRow = row + d[0] * i
                endCol = col + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                            break
                        else:
                            break
                    else:
                        break
                else:
                    break


    def getQueenMoves(self, row, col, moves):
        self.getRookMoves(row, col, moves)
        self.getBishopMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        
        for i in range(8):
            endRow = row + rowMoves[i]
            endCol = col + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: # Patrat gol sau inamic
                    
                    # Mutam regele temporar in memorie
                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                        
                    # Tragem o raza sa vedem daca suntem in sah aici
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    
                    if not inCheck:
                        moves.append(Move((row, col), (endRow, endCol), self.board))
                        
                    # Punem regele inapoi la locul lui in memorie
                    if allyColor == 'w':
                        self.whiteKingLocation = (row, col)
                    else:
                        self.blackKingLocation = (row, col)

    def getRookMoves(self, row, col, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != 'Q': # Regina foloseste aceeasi logica, nu ii scoatem pin-ul din prima!
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        
        for d in directions:
            for i in range(1, 8):
                endRow = row + d[0] * i
                endCol = col + d[1] * i
                
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                            break
                        else:
                            break
                    else:
                        break # Daca e legata si o ia pe o directie ilegala, ne oprim.
                else:
                    break

    #Calculam toate mutarile posibile la un moment dat

    def allPossibleMoves(self):
        moves = []
        boardLen = len(self.board)
        boardHeight = len(self.board[0])
        for row in range(boardLen):
            for col in range(boardHeight):
                turn = self.board[row][col][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[row][col][1]
                    
                    if piece == 'P':
                        self.getPawnMoves(row, col, moves)
                    if piece == 'N':
                        self.getNightMoves(row, col, moves)
                    if piece == 'B':
                        self.getBishopMoves(row, col, moves)
                    if piece == 'Q':
                        self.getQueenMoves(row, col, moves)
                    if piece == 'K':            
                        self.getKingMoves(row, col, moves)
                    if piece == 'R':
                        self.getRookMoves(row, col, moves)
        return moves


    #Filtram mutarile toate mutarile posibile luand in considerare anumite reguli

    def allValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]

        if self.inCheck:
            if len(self.checks) == 1: # Sah de la o singura piesa
                moves = self.allPossibleMoves()
                
                # Extragem informatiile despre piesa care da sah
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                
                # Lista patratelor pe care putem muta ca sa scapam de sah
                validSquares = []
                
                # Daca e cal, trebuie sa il capturam (nu poti bloca un cal)
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    # Daca e alta piesa, putem muta pe oricare patrat dintre ea si rege
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # Am ajuns la piesa inamica
                            break
                            
                # Filtram mutarile: stergem ce nu rezolva sahul
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K': # Mutarile regelui sunt filtrate separat in getKingMoves
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else: 
                # Sah dublu! Singura varianta e sa fugi cu Regele.
                self.getKingMoves(kingRow, kingCol, moves) 
        else: 
            # Nu e sah, generam mutari normale (care vor tine cont de pins)
            moves = self.allPossibleMoves()
            
        # Logica ta de Mat si Pat ramane neschimbata
        if len(moves) == 0:
            if self.inCheck:
                self.checkMate = True
                print("MAT")
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False    
            
        return moves
    


    def checkForPinsAndChecks(self):
        pins = []  
        checks = []  
        inCheck = False
        
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () 
            
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == (): 
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                            
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        if (0 <= j <= 3 and type == 'R') or \
                           (4 <= j <= 7 and type == 'B') or \
                           (i == 1 and type == 'P' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                           (type == 'Q') or (i == 1 and type == 'K'):
                           
                            if possiblePin == (): 
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: 
                                pins.append(possiblePin)
                                break
                        else:
                            break
                else:
                    break 

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N': 
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
                    
        return inCheck, pins, checks

        

class Move():


    """

    Conversie notatie din sah in coordonate ale matricei

    """
    ranksToRows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4,
                   "5" : 3, "6" : 2, "7" : 1, "8" : 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}

    filesToCols = {"a" : 0, "b" : 1, "c" : 2, "d" : 3, "e" : 4, "f" : 5, "g" : 6, "h" : 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSquare, endSquare, board):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False 

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
        
    def getRankFile(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]
    
