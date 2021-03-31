import math
import pickle
from linebot import LineBotApi
from linebot.models import TextSendMessage
import random
from tables import db, TicTacToe, LineAccount
from math import inf
HUMAN = -1
COMPUTER = 1


class Board:
    META_DICT = {
        2: "O",
        0: "  ",
        1: "X",
        -1: "1",
        -2: "2",
        -3: "3",
        -4: "4",
        -5: "5",
        -6: "6",
        -7: "7",
        -8: "8",
        -9: "9"
    }

    def __init__(self):
        self.board = [
            [-1, -2, -3],
            [-4, -5, -6],
            [-7, -8, -9]]
        self.turn = 1
        self.status = 0

    def write(self, point):
        try:
            point = int(point)
        except ValueError:
            return False
        if not 0 < point < 10:
            return False
        x = (point + 2) % 3
        y = math.ceil(point / 3) - 1
        if 0 <= x < 3 and 0 <= y < 3 and self.board[y][x] < 0:
            self.board[y][x] = self.turn
            if self.turn == 1:
                self.turn = 2
            elif self.turn == 2:
                self.turn = 1
            return True
        return False

    def check_stat(self):
        is_x_cross1 = True
        is_x_cross2 = True
        is_o_cross1 = True
        is_o_cross2 = True
        is_draw = True
        for i in range(3):
            is_x_ver = True
            is_o_ver = True
            is_x_hor = True
            is_o_hor = True
            for j in range(3):
                vertical_value = self.board[j][i]
                horizontal_value = self.board[i][j]
                if is_x_ver and vertical_value != 1:
                    is_x_ver = False
                if is_o_ver and vertical_value != 2:
                    is_o_ver = False
                if is_x_hor and horizontal_value != 1:
                    is_x_hor = False
                if is_o_hor and horizontal_value != 2:
                    is_o_hor = False
                if i == j:
                    if is_x_cross1 and horizontal_value != 1:
                        is_x_cross1 = False
                    if is_o_cross1 and horizontal_value != 2:
                        is_o_cross1 = False
                elif i + j == 2:
                    if is_x_cross2 and horizontal_value != 1:
                        is_x_cross2 = False
                    if is_o_cross2 and horizontal_value != 2:
                        is_o_cross2 = False
                if vertical_value < 0:
                    is_draw = False
            if is_x_hor or is_x_ver:
                return 1
            if is_o_hor or is_o_ver:
                return 2
        if is_x_cross1 or is_x_cross2:
            return 1
        if is_o_cross1 or is_o_cross2:
            return 2
        if is_draw:
            return -1
        return 0

    def reset(self):
        self.board = [
            [-1, -2, -3],
            [-4, -5, -6],
            [-7, -8, -9]]
        self.turn = 1
        self.status = 0

    def get_board_str(self):
        res = []
        for row in self.board:
            res.append(" " + " | ".join(self.META_DICT[x] for x in row))
        return "\n------------\n".join(res)


class ComputerBoard:
    META_DICT = {
        COMPUTER: "O",
        0: "  ",
        HUMAN: "X"
    }

    def __init__(self):
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]
        self.turn = random.choice([1, -1])
        self.status = 0

    def write(self, point=None, x=None, y=None):
        if point:
            point = int(point)
            if not 0 < point < 10:
                return False
            x = (point + 2) % 3
            y = math.ceil(point/3) - 1
        if 0 <= x < 3 and 0 <= y < 3 and self.board[y][x] == 0:
            self.board[y][x] = self.turn
            self.change_turn()
            return True
        return False

    def evaluate(self, check_board=None):
        status = self.check_stat(check_board)
        if status == COMPUTER:
            return 1
        if status == HUMAN:
            return -1
        return 0

    def game_over(self):
        status = self.check_stat()
        return status == 1 or status == -1

    def check_stat(self, check_board=None):
        if not check_board:
            check_board = self.board
        is_x_cross1 = True
        is_x_cross2 = True
        is_o_cross1 = True
        is_o_cross2 = True
        is_draw = True
        for i in range(3):
            is_x_ver = True
            is_o_ver = True
            is_x_hor = True
            is_o_hor = True
            for j in range(3):
                vertical_value = check_board[j][i]
                horizontal_value = check_board[i][j]
                if is_x_ver and vertical_value != HUMAN:
                    is_x_ver = False
                if is_o_ver and vertical_value != COMPUTER:
                    is_o_ver = False
                if is_x_hor and horizontal_value != HUMAN:
                    is_x_hor = False
                if is_o_hor and horizontal_value != COMPUTER:
                    is_o_hor = False
                if i == j:
                    if is_x_cross1 and horizontal_value != HUMAN:
                        is_x_cross1 = False
                    if is_o_cross1 and horizontal_value != COMPUTER:
                        is_o_cross1 = False
                if i+j == 2:
                    if is_x_cross2 and horizontal_value != HUMAN:
                        is_x_cross2 = False
                    if is_o_cross2 and horizontal_value != COMPUTER:
                        is_o_cross2 = False
                if vertical_value == 0:
                    is_draw = False
            if is_x_hor or is_x_ver:
                return HUMAN
            if is_o_hor or is_o_ver:
                return COMPUTER
        if is_x_cross1 or is_x_cross2:
            return HUMAN
        if is_o_cross1 or is_o_cross2:
            return COMPUTER
        if is_draw:
            return 0
        return -2

    def reset(self):
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]
        self.turn = 1
        self.status = 0

    def get_board_str(self):
        res = []
        for row in self.board:
            res.append(" " + " | ".join(self.META_DICT[x] for x in row))
        return "\n--------------\n".join(res)

    def change_turn(self):
        self.turn *= -1

    def minimax(self, depth, turn, count=0):
        if turn == COMPUTER:
            best = [-1, -1, -inf, 0]
        else:
            best = [-1, -1, +inf, 0]
        if depth == 0 or self.game_over():
            score = self.check_stat()
            return [-1, -1, score, count]
        cells = self.empty_cells()
        random.shuffle(cells)
        for cell in cells:
            x, y = cell
            self.board[y][x] = turn
            score = self.minimax(depth - 1, -turn, count + 1)
            self.board[y][x] = 0
            score[0], score[1] = x, y
            if turn == COMPUTER:
                if (best[2] == score[2] and best[3] < count) or score[2] > best[2]:
                    best = score
            else:
                if (best[2] == score[2] and best[3] < count) or score[2] < best[2]:
                    best = score
        return best

    def empty_cells(self):
        cells = []
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell == 0:
                    cells.append([x, y])
        return cells

    def ai_turn(self):
        depth = len(self.empty_cells())
        if depth == 0 or self.game_over():
            return

        if depth == 9:
            x = random.choice([0, 1, 2])
            y = random.choice([0, 1, 2])
        else:
            move = self.minimax(depth, COMPUTER)
            x, y = move[0], move[1]
        self.write(x=x, y=y)

    def play(self, message, reply_token, line_bot_api: LineBotApi):
        messages = []
        game_over = False
        if self.turn == COMPUTER:
            self.ai_turn()
            messages.append(TextSendMessage("Computer turn\n\n" + self.get_board_str()))
            messages.append(TextSendMessage("Your turn, type 1-9"))
        elif len(self.empty_cells()) == 9 and message.lower() == "/tictactoecomp":
            messages.append(TextSendMessage(self.get_board_str()))
            messages.append(TextSendMessage("Your turn, type 1-9"))
        else:
            if self.write(message):
                messages.append(TextSendMessage(self.get_board_str()))
                status = self.check_stat()
                if status == -2:
                    self.ai_turn()
                    messages.append(TextSendMessage("Computer turn\n\n" + self.get_board_str()))
                    status = self.check_stat()
                    if status == -2:
                        messages.append(TextSendMessage("Your turn, type 1-9"))
                if status != -2:
                    game_over = True
                    if status == HUMAN:
                        messages.append(TextSendMessage("You win!"))
                    elif status == COMPUTER:
                        messages.append(TextSendMessage("You lose!"))
                    else:
                        messages.append(TextSendMessage("Draw game."))
            else:
                messages.append(TextSendMessage("Wrong input."))
        line_bot_api.reply_message(
            reply_token,
            messages
        )
        return game_over


def play(room_id, player, message, reply_token, line_bot_api: LineBotApi, against_comp=False):
    def get_player_name(next_turn=True):
        if (board.turn == 1 and next_turn) or (board.turn == 2 and not next_turn):
            return LineAccount.query.get(tic_tac_toe.first_player).name
        for account in tic_tac_toe.players:
            if account.account_id != tic_tac_toe.first_player:
                return account.name

    tic_tac_toe = TicTacToe.query.get(room_id)
    if against_comp:
        if not tic_tac_toe:
            tic_tac_toe = TicTacToe(id=room_id)
            tic_tac_toe.players = [player]
            board = ComputerBoard()
            tic_tac_toe.board = pickle.dumps(board)
            db.session.add(tic_tac_toe)
        else:
            if message.lower() == "/exit":
                tic_tac_toe.is_playing = False
                tic_tac_toe.players.clear()
                db.session.commit()
                line_bot_api.reply_message(reply_token,
                                           TextSendMessage("TicTacToe Exited."))
                return True
            elif not tic_tac_toe.is_playing:
                tic_tac_toe.is_playing = True
                tic_tac_toe.players = [player]
                board = ComputerBoard()
            else:
                board = pickle.loads(tic_tac_toe.board)
            if board.play(message, reply_token, line_bot_api):
                tic_tac_toe.is_playing = False
                tic_tac_toe.players.clear()
            else:
                tic_tac_toe.board = pickle.dumps(board)
            db.session.commit()
            return True

    else:
        if not tic_tac_toe:
            tic_tac_toe = TicTacToe(id=room_id)
            tic_tac_toe.players.append(player)
            player.name = line_bot_api.get_profile(player.account_id).display_name
            board = Board()
            tic_tac_toe.board = pickle.dumps(board)
            db.session.add(tic_tac_toe)
            db.session.commit()
            line_bot_api.reply_message(reply_token,
                                       TextSendMessage("1 more player, /tictactoe to join."))
            return True
        else:
            if message.lower() == "/exit":
                tic_tac_toe.is_playing = False
                tic_tac_toe.players.clear()
                db.session.commit()
                line_bot_api.reply_message(reply_token,
                                           TextSendMessage("TicTacToe Exited."))
                return True
            elif not tic_tac_toe.is_playing:
                tic_tac_toe.is_playing = True
                tic_tac_toe.players.append(player)
                player.name = line_bot_api.get_profile(player.account_id).display_name
                board = Board()
                tic_tac_toe.board = pickle.dumps(board)
                db.session.commit()
                line_bot_api.reply_message(reply_token,
                                           TextSendMessage("1 more player, /tictactoe to join."))
                return True
            else:
                board = pickle.loads(tic_tac_toe.board)
                if player not in tic_tac_toe.players:
                    if len(tic_tac_toe.players) < 2:
                        tic_tac_toe.players.append(player)
                        tic_tac_toe.first_player = random.choice(tic_tac_toe.players).account_id
                        player.name = line_bot_api.get_profile(player.account_id).display_name
                        db.session.commit()
                        line_bot_api.reply_message(reply_token,
                                                   TextSendMessage(board.get_board_str() +
                                                                   f"\n{get_player_name()} TURN\n"
                                                                   f"Type 1-9\n"
                                                                   f"/exit to end the game."))
                    else:
                        line_bot_api.reply_message(reply_token,
                                                   TextSendMessage("There is currently game playing."))
                    return True

        if board.status == 0:
            if (player.account_id == tic_tac_toe.first_player and board.turn == 1) \
                    or (player.account_id != tic_tac_toe.first_player and board.turn == 2) and len(tic_tac_toe.players) == 2:
                if board.write(message):
                    board.status = board.check_stat()
                else:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage("Wrong input."))
                    return True
                if board.status != 0:
                    if board.status == 1 or board.status == 2:
                        line_bot_api.reply_message(reply_token,
                                                   TextSendMessage(board.get_board_str() +
                                                                   f"\n{get_player_name(False)} WON"))
                    elif board.status == -1:
                        line_bot_api.reply_message(reply_token,
                                                   TextSendMessage(board.get_board_str() + "\nDRAW"))
                    tic_tac_toe.is_playing = False
                    tic_tac_toe.players.clear()
                    db.session.commit()
                else:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage(board.get_board_str() +
                                                               f"\n{get_player_name()} TURN\n"
                                                               f"Type 1-9\n"
                                                               f"/exit to end the game."))
                    tic_tac_toe.board = pickle.dumps(board)
                    db.session.commit()
                return True
            else:
                return False



