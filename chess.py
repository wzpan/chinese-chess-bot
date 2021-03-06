#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random

from elephantfish import *


def get_menu():
    return """功能菜单：
/开局
    开一局游戏
/下棋 行1列1行2列2
    根据步法下棋
    示例： /下棋 h2e2
/悔棋
    悔一步棋
/投降
    投降认输。只有开局的人才能投降
"""


def get_ack():
    acks = [
        "这可难不到我。",
        "小意思啦",
        "我的灵感来了。",
        "你有点腻害哦~",
        "真是出乎意料的下法！",
        "我感觉我的战斗力正在提升",
        "让我喝口水先！",
        "压力来了>_<",
        "你在放水吗?",
        "我的脑袋疼!",
        "这就是强者的气息吗？",
    ]
    return random.choice(acks)


class ChessGame:
    """
    对 bupticybee/elephantfish 的封装    
    """
    def __init__(self):
        self.hist = [Position(initial, 0)]  # 历史记录
        self.searcher = Searcher()  # 解法查找器

    def parse(self, c):
        fil, rank = ord(c[0]) - ord("a"), int(c[1])
        return A0 + fil - 16 * rank

    def render(self, i):
        rank, fil = divmod(i - A0, 16)
        return chr(fil + ord("a")) + str(-rank)

    def get_board(self, pos):
        """
        获得象棋棋盘文本
        """
        res = ""
        uni_pieces = {
            "R": "车",
            "N": "马",
            "B": "相",
            "A": "仕",
            "K": "帅",
            "P": "兵",
            "C": "炮",
            "r": "俥",
            "n": "傌",
            "b": "象",
            "a": "士",
            "k": "将",
            "p": "卒",
            "c": "砲",
            ".": "．",
        }
        for i, row in enumerate(pos.board.split()):
            res += " {} {}\n".format(9 - i, "".join(uni_pieces.get(p, p) for p in row))
        res += "    ａｂｃｄｅｆｇｈｉ"
        return res

    def get_computer_board(self):
        """
        获得电脑走完后（或者初始）的棋盘
        """
        return self.get_board(self.hist[-1])

    def get_player_board(self):
        """
        获得玩家走完后的棋盘
        """
        return self.get_board(self.hist[-1].rotate())

    def move(self, move_str) -> str:
        """
        玩家下棋
        
        :param move_str: 下棋的走法表示字符串，例如 h2e2
        :return: 是否有效下棋, 对应的提示信息
        """
        match = re.match("([a-i][0-9])" * 2, move_str)
        move = self.parse(match.group(1)), self.parse(match.group(2))

        if move in self.hist[-1].gen_moves():
            self.hist.append(self.hist[-1].move(move))
            return True, self.get_player_board()
        else:
            return False, "走法不合法，请使用 `/下棋` 指令重试"

    def cancel(self):
        """
        玩家悔棋
        """
        if len(self.hist) > 2:
            self.hist.pop()
            self.hist.pop()
            return "好吧，让你悔一步棋\n\n" + self.get_computer_board()
        else:
            return "当前已经没有可以悔棋的步骤啦"

    def response(self):
        """
        电脑下棋及结果判断
        
        :return: 是否结束游戏, 提示信息
        """
        if self.hist[-1].score <= -MATE_LOWER:
            self.hist.clear()
            return True, "\n恭喜，您赢了！\n"

        _, move, score = self.think()

        ret = ""

        if score == MATE_UPPER:
            ret += "将军！\n"

        ret += get_ack() + "\n我的下一着：{}\n".format(
            self.render(255 - move[0] - 1) + self.render(255 - move[1] - 1)
        )

        self.hist.append(self.hist[-1].move(move))

        ret += self.get_computer_board()

        if len(self.hist) > 4:
            self.hist.pop(0)
            self.hist.pop(0)

        if self.hist[-1].score <= -MATE_LOWER:
            self.hist.clear()
            return True, ret + "\n\n游戏结束，您输了。"

        return False, ret

    def think(self):
        """
        电脑思考
        
        在限定时间内完成下一步的思考，并返回走法。
        可以通过调整 `TIME_LIMIT` 来设置电脑的最长思考时间。
        值越长，电脑越强，但响应时间也会越久。
        """
        start = time.time()
        for _depth, move, score in self.searcher.search(self.hist[-1], self.hist):
            if time.time() - start > THINK_TIME:
                break
        return _depth, move, score


if __name__ == "__main__":
    game = ChessGame()
    game.next("a0a1")
    game.next("a1a2")
