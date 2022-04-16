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

from chess import ChessGame
from chess import get_menu
from command_register import command
from utils import give_role
from utils import is_admin
from utils import send_message

config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yml"))
TOKEN = qqbot.Token(config["bot"]["appid"], config["bot"]["token"])
ENABLE_HORNOR = config["hornor_role"]["enable"]
if ENABLE_HORNOR:
    ROLE_INFO = qqbot.RoleUpdateInfo(config["hornor_role"]["name"], 
                                    config["hornor_role"]["color"],
                                    1)
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
    await send_message("请输入正确的步法。例如 /下棋 h2e2", event, message)
    return True

def _is_surrenderable(guild_id: str, channel_id: str, user_id: str):
    """
    是否可以结束游戏
    只有开局的人和管理员才能结束游戏
    """
    game = _get_game_by_channel_id(channel_id)
    return is_admin(TOKEN, guild_id, user_id) or (game and game['creator'] == user_id)

def _give_hornor(guild_id: str, user_id: str):    
    api = qqbot.UserAPI(TOKEN, False)
    if ENABLE_HORNOR and is_admin(TOKEN, guild_id, api.me().id):
        qqbot.logger.info("颁发象棋大师身份组")
        give_role(TOKEN, guild_id, user_id, ROLE_INFO)
    else:
        qqbot.logger.info("不颁发象棋大师身份组")

@command("开局")
async def start_game(params: str, event: str, message: qqbot.Message):
    if message.channel_id in GAME_DATA:
        ret = "游戏已经开始了，请等待下一局。您也可以使用 `/投降` 指令提前结束游戏。"
    else:
        game = ChessGame()
        GAME_DATA[message.channel_id] = {
            "creator": message.author.id,
            "game": game
        }
        ret = game.get_computer_board()
    await send_message(TOKEN, ret, event, message)
    return True


@command("菜单")
async def ask_menu(params: str, event: str, message: qqbot.Message):
    ret = get_menu()
    await send_message(TOKEN, ret, event, message)
    return True


@command("投降")
async def surrender(params: str, event: str, message: qqbot.Message):
    game_data = _get_game_by_channel_id(message.channel_id)
    if game_data:
        if _is_surrenderable(message.guild_id, message.channel_id, message.author.id):
            GAME_DATA.pop(message.channel_id)
            ret = "游戏结束，您输了。"
        else:
            ret = "只有开局的人或者管理员才可以结束游戏哦"            
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
    await send_message(TOKEN, ret, event, message)
    return True

async def do_move(params: str, event: str, message: qqbot.Message):
    game_data = _get_game_by_channel_id(message.channel_id)    
    if game_data:
        game = game_data['game']
        res, ret = game.move(params)        
        await send_message(TOKEN, ret, event, message)
        if res:
            is_end, ret = game.response()            
            if is_end:
                GAME_DATA.pop(message.channel_id)
                if '您赢了' in ret and event != "DIRECT_MESSAGE_CREATE":
                    _give_hornor(message.guild_id, message.author.id)
                    ret += "\n\n👑恭喜获得新身份组【{}】".format(ROLE_INFO.name)
            await send_message(TOKEN, ret, event, message)
    else:
        ret = "游戏还没开始。您可以使用 `/开局` 指令开始游戏。"
        await send_message(TOKEN, ret, event, message)

@command("下棋", validate_func=_validate_func, invalid_func=_invalid_func)
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
    await send_message(TOKEN, "抱歉，没明白你的意思呢。" + get_menu(), event, message)

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
    qqbot.async_listen_events(TOKEN, False, qqbot_handler, qqbot_direct_handler)


if __name__ == "__main__":
    run()
