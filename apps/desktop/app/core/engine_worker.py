import chess
import chess.engine
from PyQt6.QtCore import QThread, pyqtSignal
import os

class EngineWorker(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, engine_path, threads, hash_size):
        super().__init__()
        self.engine_path = engine_path
        self.threads = threads
        self.hash_size = hash_size
        self.uci_moves = []
        self.is_running = True
        self.needs_restart = False
        
        # --- NOU: Gestiunea dinamica a liniilor ---
        self.num_lines = 3
        self.lines = {i: "" for i in range(1, self.num_lines + 1)}

    def update_position(self, uci_moves):
        self.uci_moves = uci_moves
        self.needs_restart = True
        
    def set_lines(self, num_lines):
        """Schimba numarul de linii analizate din mers"""
        self.num_lines = num_lines
        self.needs_restart = True

    def run(self):
        if not os.path.exists(self.engine_path):
            self.update_signal.emit(f"EROARE: Nu s-a gasit executabilul la:\n{self.engine_path}")
            return

        try:
            engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            engine.configure({
                "Threads": self.threads, 
                "Hash": self.hash_size
            })
        except Exception as e:
            self.update_signal.emit(f"Eroare la pornirea Stockfish: {e}")
            return

        board = chess.Board()

        while self.is_running:
            if self.needs_restart:
                board = chess.Board()
                for move in self.uci_moves:
                    board.push_uci(move)
                self.needs_restart = False
                # Resetam dictionarul de linii pentru noua dimensiune
                self.lines = {i: "" for i in range(1, self.num_lines + 1)}

            # --- NOU: Folosim self.num_lines in loc de valoarea hardcodata 3 ---
            with engine.analysis(board, multipv=self.num_lines) as analysis:
                for info in analysis:
                    if not self.is_running or self.needs_restart:
                        break

                    if "score" in info and "pv" in info:
                        depth = info.get("depth", 0)
                        score = info["score"].white()
                        
                        if score.is_mate():
                            score_str = f"M{score.mate()}"
                        else:
                            score_str = f"{score.score() / 100:+.2f}"

                        temp_board = board.copy()
                        pv_san_list = []
                        for m in info["pv"][:6]: 
                            try:
                                pv_san_list.append(temp_board.san(m)) 
                                temp_board.push(m) 
                            except:
                                break 
                                
                        pv_moves = " ".join(pv_san_list)
                        multipv = info.get("multipv", 1)
                        
                        # Salvam doar liniile care sunt in limita ceruta
                        if multipv <= self.num_lines:
                            self.lines[multipv] = f"{score_str} | Adancime: {depth} | {pv_moves}"
                        
                        # Asamblam liniile ignorand intrarile goale
                        output_lines = [self.lines.get(i, "") for i in range(1, self.num_lines + 1) if self.lines.get(i, "") != ""]
                        output = "\n".join(output_lines)
                        self.update_signal.emit(output)
                        
        engine.quit()
    
    def stop(self):
        self.is_running = False
        self.needs_restart = True
        self.wait()