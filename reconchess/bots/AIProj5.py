import chess.engine
import random
from reconchess import *
import os
import csv

STOCKFISH_ENV_VAR = 'STOCKFISH_EXECUTABLE'

class AIPROJ5(Player):
    """
    TroutBot uses the Stockfish chess engine to choose moves. In order to run TroutBot you'll need to download
    Stockfish from https://stockfishchess.org/download/ and create an environment variable called STOCKFISH_EXECUTABLE
    that is the path to the downloaded Stockfish executable.
    """

    def __init__(self):
        self.board = None
        self.color = None
        self.my_piece_captured_square = None
        self.found_king = False
        self.king_pos = None
        self.turn = 0
        self.num_pieces = 16
        self.captured_num = 0
        self.endgamePieces = [chess.D7, chess.B7,
                              chess.G7, chess.D5,
                              chess.G5, chess.B5,
                              chess.B3, chess.D3,
                              chess.G3, chess.B2,
                              chess.D2, chess.G2]
        self.piece_values = {'P':1, 'N': 3, 'B': 3, 'R': 5, 'Q':9, 'K': 20}

        # make sure stockfish environment variable exists
        if STOCKFISH_ENV_VAR not in os.environ:
            raise KeyError(
                'TroutBot requires an environment variable called "{}" pointing to the Stockfish executable'.format(
                    STOCKFISH_ENV_VAR))

        # make sure there is actually a file
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))

        # initialize the stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)


    def handle_game_start(self, color: Color, board: chess.Board):
        self.board = board
        self.color = color

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        # if the opponent captured our piece, remove it from our board.
        self.my_piece_captured_square = capture_square
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Square:

        # Beginning
        if (self.turn == 0):
            return chess.B5
        elif (self.turn==1):
            return chess.G5



        # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            self.num_pieces -= 1
            return self.my_piece_captured_square


        # End
        # Figure out where the king is
        # The average game
        # If we have less than 7 of our pieces or if they have less than 7 pieces
        if (self.num_pieces < 7 or self.captured_num >= 16-7):
            if len(self.endgamePieces > 0 and not self.found_king):
                possibleKing = self.endgamePieces.pop()
                if (self.board.piece_at(possibleKing) == chess.KING):
                    self.found_king = True
                    self.king_pos = possibleKing
                return possibleKing
            elif self.found_king:
                return self.king_pos


        # Middle Section
        else:

            # if we might capture a piece when we move, sense where the capture will occur
            future_move = self.choose_move(move_actions, seconds_left)
            if future_move is not None and self.board.piece_at(future_move.to_square) is not None:

                return future_move.to_square

            # otherwise, just randomly choose a sense action, but don't sense on a square where our pieces are located
            for square, piece in self.board.piece_map().items():
                if piece.color == self.color:
                    sense_actions.remove(square)

            return random.choice(sense_actions)

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        # add the pieces in the sense result to our board
        for square, piece in sense_result:
            self.board.set_piece_at(square, piece)


    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        self.turn += 1
        # if we might be able to take the king, try to
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)

        # otherwise, try to move with the stockfish chess engine
        try:
            self.board.turn = self.color
            self.board.clear_stack()
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            return result.move
        except (chess.engine.EngineError, chess.engine.EngineTerminatedError) as e:
            print('Engine bad state at "{}"'.format(self.board.fen()))
            return random.choice(move_actions + [None])

        # if all else fails, pass
        return None

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # if a move was executed, apply it to our board
        if captured_opponent_piece == True:
            self.captured_num += 1

        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        self.engine.quit()


