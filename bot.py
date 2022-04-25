#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py: 象棋大师的主程序

author: wzpan
email: m@hahack.com
"""
from __future__ import annotations

import re

import qqbot

from chess import ChessGame, get_menu
from command_register import Bot, CheckFailed
from utils import give_role, is_admin, send_message


class ChineseChessBot(Bot):

    def __init__(self, prefix: str):
        super().__init__(prefix)
        self.enable_honor = self.config["honor_role"]["enable"]
        self.role_info = qqbot.RoleUpdateInfo(
            self.config["honor_role"]["name"], self.config["honor_role"]["color"], 1
        )
        self.game_data = {}

    async def handle_message(self, event: str, message: qqbot.Message):
        message.content = re.sub(r'<@\![0-9]+>', '', message.content).strip()
        if await self.process_commands(event, message):
            return
        params = message.content.split()
        params = params[0] if params else ""
        if _validate_func(params):
            await do_move(params, event, message)
            return
        await send_message(self.token, "抱歉，没明白你的意思呢。" + get_menu(), event, message)


bot = ChineseChessBot(prefix='/')


def _get_game_by_channel_id(channel_id: str):
    """
    根据 channel_id 获取对应的游戏
    """
    return bot.game_data.get(channel_id, None)


def _validate_func(param):
    return param and re.match(".*([a-i][0-9])([a-i][0-9])", param)


async def _invalid_func(error: BaseException, params: str, event: str, message: qqbot.Message):
    """
    当参数不符合要求时的处理函数
    """
    if isinstance(error, CheckFailed):
        await send_message(bot.token, "请输入正确的步法。例如 /下棋 h2e2", event, message)


def _is_surrenderable(guild_id: str, channel_id: str, user_id: str):
    """
    是否可以结束游戏
    只有开局的人和管理员才能结束游戏
    """
    game = _get_game_by_channel_id(channel_id)
    return is_admin(bot.token, guild_id, user_id) or (game and game["creator"] == user_id)


def _give_honor(guild_id: str, user_id: str):
    api = qqbot.UserAPI(bot.token, False)
    if bot.enable_honor and is_admin(bot.token, guild_id, api.me().id):
        qqbot.logger.info("颁发象棋大师身份组")
        give_role(bot.token, guild_id, user_id, bot.role_info)
    else:
        qqbot.logger.info("不颁发象棋大师身份组")


@bot.command("开局")
async def start_game(params: str, event: str, message: qqbot.Message):
    qqbot.logger.info("开局")
    if message.channel_id in bot.game_data:
        ret = "游戏已经开始了，请等待下一局。您也可以使用 `/投降` 指令提前结束游戏。"
    else:
        game = ChessGame()
        bot.game_data[message.channel_id] = {"creator": message.author.id, "game": game}
        ret = game.get_computer_board()
    await send_message(bot.token, ret, event, message)
    return True


@bot.command("菜单")
async def ask_menu(params: str, event: str, message: qqbot.Message):
    qqbot.logger.info("菜单")
    ret = get_menu()
    await send_message(bot.token, ret, event, message)
    return True


@bot.command("投降")
async def surrender(params: str, event: str, message: qqbot.Message):
    qqbot.logger.info("投降")
    game_data = _get_game_by_channel_id(message.channel_id)
    if game_data:
        if _is_surrenderable(message.guild_id, message.channel_id, message.author.id):
            bot.game_data.pop(message.channel_id)
            ret = "游戏结束，您输了。"
        else:
            ret = "只有开局的人或者管理员才可以结束游戏哦"
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
    await send_message(bot.token, ret, event, message)
    return True


async def do_move(params: str, event: str, message: qqbot.Message):
    game_data = _get_game_by_channel_id(message.channel_id)
    if game_data:
        game = game_data["game"]
        res, ret = game.move(params)
        await send_message(bot.token, ret, event, message)
        if res:
            is_end, ret = game.response()
            if is_end:
                bot.game_data.pop(message.channel_id)
                if "您赢了" in ret and event != "DIRECT_MESSAGE_CREATE":
                    _give_honor(message.guild_id, message.author.id)
                    ret += "\n\n👑恭喜获得新身份组【{}】".format(bot.role_info.name)
            await send_message(bot.token, ret, event, message)
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
        await send_message(bot.token, ret, event, message)


@bot.command("下棋", checks=_validate_func, on_error=_invalid_func)
async def move(params: str, event: str, message: qqbot.Message):
    qqbot.logger.info("下棋")
    await do_move(params, event, message)
    return True


@bot.command("悔棋")
async def cancel(params: str, event: str, message: qqbot.Message):
    qqbot.logger.info("悔棋")
    game_data = _get_game_by_channel_id(message.channel_id)
    if game_data:
        game = game_data["game"]
        ret = game.cancel()
        await send_message(bot.token, ret, event, message)
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
        await send_message(bot.token, ret, event, message)
    return True


def run():
    """
    启动机器人
    """
    # @机器人后推送被动消息
    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, bot.handle_message
    )
    # 私信消息
    qqbot_direct_handler = qqbot.Handler(
        qqbot.HandlerType.DIRECT_MESSAGE_EVENT_HANDLER, bot.handle_message
    )
    qqbot.async_listen_events(bot.token, False, qqbot_handler, qqbot_direct_handler)


if __name__ == "__main__":
    run()
