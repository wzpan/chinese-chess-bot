#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py: 象棋大师的主程序

author: wzpan
email: m@hahack.com
"""

import os.path
import re

import qqbot
from qqbot.core.util.yaml_util import YamlUtil

from command_register import command
from chess import ChessGame, get_menu


config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yml"))
T_TOKEN = qqbot.Token(config["bot"]["appid"], config["bot"]["token"])
GAME_DATA = {}

def _get_game_by_channel_id(channel_id: str):
    """
    根据 channel_id 获取对应的游戏
    """
    return GAME_DATA.get(channel_id, None)

def _validate_func(param):
    return param and re.match('([a-i][0-9])'*2, param)

async def _invalid_func(event: str,  message: qqbot.Message):
    """
    当参数不符合要求时的处理函数
    """
    await _send_message("请输入正确的步法。例如 /下棋 h2e2", event, message)
    return True

async def _send_message(content: str, event: str, message: qqbot.Message):
    """
    机器人发送消息
    """
    msg_api = qqbot.AsyncMessageAPI(T_TOKEN, False)
    dms_api = qqbot.AsyncDmsAPI(T_TOKEN, False)

    send = qqbot.MessageSendRequest(content, message.id)
    if event == "DIRECT_MESSAGE_CREATE":
        await dms_api.post_direct_message(message.guild_id, send)
    else:
        await msg_api.post_message(message.channel_id, send)

@command("/开局")
async def start_game(params: str, event: str, message: qqbot.Message):
    if message.channel_id in GAME_DATA:
        ret = "游戏已经开始了，请等待下一局。您也可以使用 `/投降` 指令提前结束游戏。"
    else:
        game = ChessGame()
        GAME_DATA[message.channel_id] = game
        ret = game.get_computer_board()
    await _send_message(ret, event, message)
    return True


@command("/菜单")
async def ask_menu(params: str, event: str, message: qqbot.Message):
    ret = get_menu()
    await _send_message(ret, event, message)
    return True


@command("/投降")
async def surrender(params: str, event: str, message: qqbot.Message):
    if message.channel_id in GAME_DATA:
        GAME_DATA.pop(message.channel_id)
        ret = "游戏结束，您输了。"
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
    await _send_message(ret, event, message)
    return True

async def do_move(params: str, event: str, message: qqbot.Message):
    game = _get_game_by_channel_id(message.channel_id)
    if game:
        res, ret = game.move(params)        
        await _send_message(ret, event, message)
        if res:
            is_end, ret = game.response()
            await _send_message(ret, event, message)
            if is_end:
                GAME_DATA.pop(message.channel_id)
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
        await _send_message(ret, event, message)

@command("/下棋", validate_func=_validate_func, invalid_func=_invalid_func)
async def move(params: str, event: str, message: qqbot.Message):
    await do_move(params, event, message)
    return True

async def _message_handler(event: str, message: qqbot.Message):
    """
    定义事件回调的处理
    :param event: 事件类型
    :param message: 事件对象（如监听消息是Message对象）
    """

    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)

    tasks = [
        ask_menu,
        start_game,
        move,
        surrender
    ]
    for task in tasks:
        if await task("", event, message):
            return
    params = message.content.split(' ')[1] if len(message.content.split(' ')) > 0 else ''
    if _validate_func(params):
        await do_move(params, event, message)
        return
    await _send_message("抱歉，没明白你的意思呢。" + get_menu(), event, message)
    

def run():
    """
    启动机器人
    """    
    # @机器人后推送被动消息
    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    # 私信消息
    qqbot_direct_handler = qqbot.Handler(
        qqbot.HandlerType.DIRECT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    qqbot.async_listen_events(T_TOKEN, False, qqbot_handler, qqbot_direct_handler)


if __name__ == "__main__":
    run()
