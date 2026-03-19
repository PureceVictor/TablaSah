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
        
        # --- NOUL SISTEM DE ARBORE ---
        self.root = MoveNode(None) # Radacina invizibila a partidei
        self.current_node = self.root # Pointer-ul care arata unde suntem acum
        # (Am sters self.moveLog)
        
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.inCheck = False
        self.pins = []
        self.checks = []

        self.enPassantPossible = ()
        self.enPassantPossibleLog = [self.enPassantPossible]

        self.currentCastleRights = CastleRight(True, True, True, True)
        self.castleRightsLog = [CastleRight(self.currentCastleRights.wks, self.currentCastleRights.bks, 
                                            self.currentCastleRights.wqs, self.currentCastleRights.bqs)]

    def makeMove(self, move): 
        # 1. LOGICA DE ARBORE (Verificam daca mutarea exista deja in variatii)
        existing_child = None
        for child in self.current_node.children:
            if child.move == move:
                existing_child = child
                break
                
        if existing_child:
            self.current_node = existing_child # Doar inaintam pe ramura existenta
        else:
            # Cream o noua ramura
            self.current_node = self.current_node.add_variation(move)

        # 2. LOGICA DE TABLA (Ramane la fel)
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved 

        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + move.promotionChoice

        if move.isEnPassantMove:
            self.board[move.startRow][move.endCol] = "--" 
            
        if move.pieceMoved[1] == 'P' and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enPassantPossible = () 
            
        self.enPassantPossibleLog.append(self.enPassantPossible)

        self.whiteToMove = not self.whiteToMove

        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.isCastleMove:
            if move.endCol - move.startCol == 2:
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = "--"
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol - 2] = "--"

        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRight(self.currentCastleRights.wks, self.currentCastleRights.bks, 
                                                self.currentCastleRights.wqs, self.currentCastleRights.bqs))

    def undoMove(self):
        # Daca pointer-ul nu este la radacina, putem da inapoi
        if self.current_node.parent is not None:
            # Luam mutarea de pe nodul curent
            move = self.current_node.move

            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured

            self.whiteToMove = not self.whiteToMove

            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = "--" 
                self.board[move.startRow][move.endCol] = move.pieceCaptured 
                
            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1]

            self.castleRightsLog.pop()
            newRights = self.castleRightsLog[-1]
            self.currentCastleRights = CastleRight(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)
            
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"
            
            # MAGIA: Mutam pointer-ul inapoi catre parinte
            self.current_node = self.current_node.parent
            
    def redoMove(self, variation_index=0):
        """Muta inainte pe Main Line (index 0) sau pe o alta variatie"""
        if len(self.current_node.children) > variation_index:
            next_node = self.current_node.children[variation_index]
            self.makeMove(next_node.move)
            # makeMove e destul de inteligent incat sa nu duplice mutarea, ci doar va inainta

    def updateCastleRights(self, move):
            # 1. Pierdem drepturile daca mutam regele sau tura
            if move.pieceMoved == "wK":
                self.currentCastleRights.wks = False
                self.currentCastleRights.wqs = False
            elif move.pieceMoved == "bK":
                self.currentCastleRights.bks = False
                self.currentCastleRights.bqs = False
            elif move.pieceMoved == "wR":
                if move.startRow == 7 and move.startCol == 0: # Turnul stang
                    self.currentCastleRights.wqs = False
                elif move.startRow == 7 and move.startCol == 7: # Turnul drept
                    self.currentCastleRights.wks = False
            elif move.pieceMoved == "bR":
                if move.startRow == 0 and move.startCol == 0: 
                    self.currentCastleRights.bqs = False
                elif move.startRow == 0 and move.startCol == 7: 
                    self.currentCastleRights.bks = False
                    
            # 2. Pierdem drepturile daca adversarul ne captureaza Tura
            if move.pieceCaptured == 'wR':
                if move.endRow == 7 and move.endCol == 0: 
                    self.currentCastleRights.wqs = False
                elif move.endRow == 7 and move.endCol == 7:
                    self.currentCastleRights.wks = False
            elif move.pieceCaptured == 'bR':
                if move.endRow == 0 and move.endCol == 0:
                    self.currentCastleRights.bqs = False
                elif move.endRow == 0 and move.endCol == 7:
                    self.currentCastleRights.bks = False
        


    
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

        #Daca randul tinta este 0 sau 7, e promovare 100%
        isPawnPromotion = False
        if row + moveAmount == 0 or row + moveAmount == 7:
            isPawnPromotion = True

        # 1. Mutarea IN FATA
        if self.board[row + moveAmount][col] == "--":
            if not piecePinned or pinDirection == (moveAmount, 0): 
                if isPawnPromotion:
                    for piece in ['Q', 'R', 'B', 'N']:
                        moves.append(Move((row, col), (row + moveAmount, col), self.board, promotionChoice=piece))
                else:
                    moves.append(Move((row, col), (row + moveAmount, col), self.board))
                
                # Mutarea dubla 
                if row == startRow and self.board[row + 2 * moveAmount][col] == "--":
                    moves.append(Move((row, col), (row + 2 * moveAmount, col), self.board))

        # 2. Capturi (Diagonala stanga)
        if col - 1 >= 0: 
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[row + moveAmount][col - 1][0] == enemyColor:
                    if isPawnPromotion:
                        for piece in ['Q', 'R', 'B', 'N']:
                            moves.append(Move((row, col), (row + moveAmount, col - 1), self.board, promotionChoice=piece))
                    else:
                        moves.append(Move((row, col), (row + moveAmount, col - 1), self.board))
                elif (row + moveAmount, col - 1) == self.enPassantPossible:
                    moves.append(Move((row, col), (row + moveAmount, col - 1), self.board, isEnPassantMove=True))
                    
        # 3. Capturi (Diagonala dreapta)
        if col + 1 <= 7: 
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[row + moveAmount][col + 1][0] == enemyColor:
                    if isPawnPromotion: 
                        for piece in ['Q', 'R', 'B', 'N']:
                            moves.append(Move((row, col), (row + moveAmount, col + 1), self.board, promotionChoice=piece))
                    else:
                        moves.append(Move((row, col), (row + moveAmount, col + 1), self.board))
                elif (row + moveAmount, col + 1) == self.enPassantPossible:
                    moves.append(Move((row, col), (row + moveAmount, col + 1), self.board, isEnPassantMove=True))
            


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
        self.getCastleMoves(row, col, moves, allyColor)

    def getCastleMoves(self, row, col, moves, allyColor):
        if self.inCheck:
            return
        if (self.whiteToMove and self.currentCastleRights.wks) or (not self.whiteToMove and self.currentCastleRights.bks):
            self.getKingSideCastleMoves(row, col, moves, allyColor)
        if (self.whiteToMove and self.currentCastleRights.wqs) or (not self.whiteToMove and self.currentCastleRights.bqs):
            self.getQueenSideCastleMoves(row, col, moves, allyColor)
        
    def getKingSideCastleMoves(self, row, col, moves, allyColor):
        if self.board[row][col+1] == "--" and self.board[row][col+2]:
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, isCastleMove = True))
    def getQueenSideCastleMoves(self, row, col, moves, allyColor):
        if self.board[row][col-1] == "--" and self.board[row][col-2] == "--" and self.board[row][col-3] == "--":
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row,col),(row, col - 2), self.board, isCastleMove = True))

    def squareUnderAttack(self, r, c):
        enemyColor = 'b' if self.whiteToMove else 'w'
        allyColor = 'w' if self.whiteToMove else 'b'
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor:
                        break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # Aceeasi logica de vizare ca la radarul mare
                        if (0 <= j <= 3 and type == 'R') or \
                           (4 <= j <= 7 and type == 'B') or \
                           (i == 1 and type == 'P' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                           (type == 'Q') or (i == 1 and type == 'K'):
                            return True # Am gasit un atacator!
                        else:
                            break # E inamic dar nu ataca pe directia asta
                else:
                    break
                    
        # Verificam caii inamici
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    return True
                    
        return False


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
    

    """
    
    FUNCTII PENTRU LOGICA DE NOTARE GRAFICA A PARTIDEI, SALVAREA ACESTEIA SI TOT CE TINE DE O INTERACTIUNE COMPLETA
    
    """
    def getNotationText(self):
        # Adaugam putin CSS pentru a arata ca niste link-uri curate
        html = "<style>a { text-decoration: none; color: #1a5f7a; font-weight: bold;} a:hover { color: #e67e22; }</style>"
        html += self._generate_tree_text(self.root, 1, True)
        return html

    def _generate_tree_text(self, node, move_number, is_white_turn):
        if not node.children:
            return ""
            
        text = ""
        main_child = node.children[0]
        
        if is_white_turn:
            text += f"<b>{move_number}.</b> "
            
        # Piesa de rezistenta: ID-ul nodului devine URL-ul link-ului!
        text += f'<a href="move:{main_child.node_id}">{main_child.move.getChessNotation()}</a> '
        
        for i in range(1, len(node.children)):
            var_child = node.children[i]
            text += "<br>&nbsp;&nbsp;&nbsp;<i>( "
            if is_white_turn:
                text += f"{move_number}. "
            else:
                text += f"{move_number}... "
                
            text += f'<a href="move:{var_child.node_id}">{var_child.move.getChessNotation()}</a> '
            text += self._generate_tree_text(var_child, move_number if is_white_turn else move_number + 1, not is_white_turn)
            text += ")</i><br>"
            
        next_move_num = move_number if is_white_turn else move_number + 1
        text += self._generate_tree_text(main_child, next_move_num, not is_white_turn)
        return text

    # 2. SISTEMUL DE TELEPORTARE (TIME TRAVEL)
    def find_node(self, current, target_id):
        """Cauta recursiv un nod in arbore dupa ID-ul lui"""
        if current.node_id == target_id:
            return current
        for child in current.children:
            found = self.find_node(child, target_id)
            if found:
                return found
        return None

    def play_to_node(self, target_node_id):
        """Teleporteaza starea partidei la nodul selectat"""
        target_node = self.find_node(self.root, target_node_id)
        if not target_node:
            return

        # Aflam drumul de la radacina pana la nodul dorit
        path = []
        curr = target_node
        while curr.parent is not None:
            path.append(curr.move)
            curr = curr.parent
        path.reverse()

        # Derulam timpul inapoi pana la pozitia de start a partidei
        while self.current_node.parent is not None:
            self.undoMove()

        # Re-aplicam mutarile pana la destinatie. 
        # makeMove e deja inteligent: nu va crea variatii noi, ci se va plimba pe cele existente!
        for move in path:
            self.makeMove(move)



    def get_clean_pgn(self):
        """Genereaza textul partidei fara tag-uri HTML pentru salvarea in fisier."""
        return self._generate_clean_text(self.root, 1, True)

    def _generate_clean_text(self, node, move_number, is_white_turn):
        if not node.children:
            return ""
        text = ""
        main_child = node.children[0]
        if is_white_turn:
            text += f"{move_number}. "
        text += f"{main_child.move.getChessNotation()} "
        for i in range(1, len(node.children)):
            var_child = node.children[i]
            text += "( "
            if is_white_turn:
                text += f"{move_number}. "
            else:
                text += f"{move_number}... "
            text += f"{var_child.move.getChessNotation()} "
            text += self._generate_clean_text(var_child, move_number if is_white_turn else move_number + 1, not is_white_turn)
            text += ") "
        next_move_num = move_number if is_white_turn else move_number + 1
        text += self._generate_clean_text(main_child, next_move_num, not is_white_turn)
        return text
        
    def load_fen(self, fen_string):
        """Placeholder pentru viitorul parser FEN"""
        print(f"[ENGINE] S-a cerut incarcarea pozitiei: {fen_string}")
        # Aici vom scrie logica de transformare a FEN-ului in matricea self.board

    def get_current_uci_path(self):
        """Returneaza lista de mutari UCI de la radacina pana la pozitia curenta"""
        path = []
        curr = self.current_node
        while curr.parent is not None:
            path.append(curr.move.get_uci())
            curr = curr.parent
        path.reverse()
        return path

        

class Move():


    """

    Conversie notatie din sah in coordonate ale matricei

    """
    ranksToRows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4,
                   "5" : 3, "6" : 2, "7" : 1, "8" : 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}

    filesToCols = {"a" : 0, "b" : 1, "c" : 2, "d" : 3, "e" : 4, "f" : 5, "g" : 6, "h" : 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSquare, endSquare, board, isEnPassantMove=False, promotionChoice='Q', isCastleMove = False):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]

        self.isPawnPromotion = False
        if (self.pieceMoved == "wP" and self.endRow == 0) or (self.pieceMoved == "bP" and self.endRow == 7):
            self.isPawnPromotion = True
            
        self.promotionChoice = promotionChoice # Q, R, B sau N

        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = "bP" if self.pieceMoved == "wP" else "wP"

        self.isCastleMove = isCastleMove

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID and self.promotionChoice == other.promotionChoice
        return False 

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
        
    def getRankFile(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]

    def get_uci(self):
        """Returneaza mutarea in format UCI (ex: e2e4, e7e8q) pt Stockfish"""
        start = self.getRankFile(self.startRow, self.startCol)
        end = self.getRankFile(self.endRow, self.endCol)
        promo = self.promotionChoice.lower() if self.isPawnPromotion else ""
        return start + end + promo


class MoveNode:
    def __init__(self, move, parent=None):
        self.move = move
        self.parent = parent
        self.children = [] # Lista de MoveNode. Index 0 = Main Line.
        
        # Generam un ID unic pentru a-l gasi usor din UI cand dam click
        self.node_id = str(id(self)) 

    def add_variation(self, move):
        """Adauga o variatie si returneaza noul nod creat"""
        new_node = MoveNode(move, parent=self)
        self.children.append(new_node)
        return new_node
        
    def promote_to_main_line(self):
        """Face ca aceasta variatie sa devina prima optiune (Main Line)"""
        if self.parent:
            self.parent.children.remove(self)
            self.parent.children.insert(0, self)


class CastleRight():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
    
