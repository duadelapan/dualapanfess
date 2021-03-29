import math
import pickle
from linebot import LineBotApi
from linebot.models import TextSendMessage

from tables import db, TicTacToe


class Board:
    META_DICT = {
        2: "O",
        0: " ",
        1: "X"
    }

    def __init__(self):
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]
        self.turn = 1
        self.status = 0

    def write(self, point):
        point = int(point)
        if not 0 < point < 10:
            return False
        x = (point + 2) % 3
        y = math.ceil(point / 3) - 1
        if 0 <= x < 3 and 0 <= y < 3 and self.board[y][x] == 0:
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
                if vertical_value == 0:
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
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]]
        self.turn = 1
        self.status = 0

    def get_board_str(self):
        res = []
        for row in self.board:
            res.append(" " + " | ".join(self.META_DICT[x] for x in row))
        return "\n".join(res)


def play(room_id, player, message, reply_token, line_bot_api: LineBotApi):
    tic_tac_toe = TicTacToe.query.get(room_id)
    print("1")
    if not tic_tac_toe:
        tic_tac_toe = TicTacToe(id=room_id)
        tic_tac_toe.players.append(player)
        player.name = line_bot_api.get_profile(player.account_id).display_name
        board = Board()
        tic_tac_toe.board = pickle.dumps(board)
        db.session.add(tic_tac_toe)
        print("added")
        db.session.commit()
        line_bot_api.reply_message(reply_token,
                                   TextSendMessage("1 more player, /tictactoe to join."))
        return True
    else:
        print("2")
        if not tic_tac_toe.is_playing:
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
                if len(tic_tac_toe) < 2:
                    tic_tac_toe.players.append(player)
                    player.name = line_bot_api.get_profile(player.account_id).display_name
                    db.session.commit()
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage(board.get_board_str() +
                                                               f"\n{tic_tac_toe.players[board.turn-1].name} TURN"))
                else:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage("There is currently game playing."))
                return True

    if board.status == 0:
        print(tic_tac_toe.players)
        if tic_tac_toe.players.index(player) == board.turn - 1:
            if board.write(message):
                board.status = board.check_stat()
            else:
                line_bot_api.reply_message(reply_token,
                                           TextSendMessage("Wrong input."))
                return True
            if board.status != 0:
                if board.status == 1:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage(board.get_board_str() + "\nX WON"))
                elif board.status == 2:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage(board.get_board_str() + "\n0 WON"))
                elif board.status == -1:
                    line_bot_api.reply_message(reply_token,
                                               TextSendMessage(board.get_board_str() + "\nDRAW"))
                tic_tac_toe.is_playing = False
                tic_tac_toe.players.clear()
                db.session.commit()
            else:
                line_bot_api.reply_message(reply_token,
                                           TextSendMessage(board.get_board_str()) +
                                           f"\n{tic_tac_toe.players[board.turn-1].name} TURN")
            return True
        else:
            return False
