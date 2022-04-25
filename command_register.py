#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
command_register: 用于指令注册

author: wzpan
email: m@hahack.com
"""
import asyncio
import os
from dataclasses import dataclass
from typing import Callable, Coroutine, TypeVar, Any, Dict

import qqbot
from qqbot.core.util.yaml_util import YamlUtil

T = TypeVar("T")
Coro = Coroutine[Any, Any, T]


class CheckFailed(Exception):
    pass


@dataclass
class Command:
    name: str
    callback: Callable[[str, str, qqbot.Message], Coro[Any]]
    checks: Callable[[str], bool]
    on_error: Callable[[BaseException, str, str, qqbot.Message], Coro[Any]]


class Bot:
    def __init__(self, prefix: str):
        self.token = qqbot.Token(
            self.config["bot"]["appid"], self.config["bot"]["token"]
        )
        self.prefix = prefix
        self.commands: Dict[str, Command] = {}

    @property
    def config(self) -> Dict[str, Any]:
        return YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yml"))

    def command(
        self,
        name: str,
        checks: Callable[[str], bool] = None,
        on_error: Callable[[BaseException, str, str, qqbot.Message], Coro[Any]] = None,
    ):
        """
        指令的装饰器
        :param name: 指令的字符串。例如 `菜单`
        :param checks: 检查函数，取唯一参数 params ，如果返回 False 则指令不会运行
        :param on_error: 指令发生错误时调用的回调
        :return: 装饰器
        """

        def decorator(func: Callable[[str, str, qqbot.Message], Coro[Any]]):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("回调必须是协程。")
            result = Command(name=name, callback=func, checks=checks, on_error=on_error)
            self.commands[name] = result
            return result

        return decorator

    async def process_commands(self, event: str, message: qqbot.Message):
        qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)
        params = message.content.removeprefix(self.prefix)
        split = params.split()
        if split[0] not in self.commands:
            return False
        invoked_command = self.commands[split[0]]
        if invoked_command.checks:
            if not invoked_command.checks(params):
                if invoked_command.on_error:
                    await invoked_command.on_error(
                        CheckFailed(), params, event, message
                    )
                return False
        param = split[1] if len(split) > 1 else ""
        qqbot.logger.info("command %s, param %s" % (invoked_command.name, param))
        try:
            await invoked_command.callback(param, event, message)
        except Exception as e:
            if invoked_command.on_error:
                await invoked_command.on_error(e, param, event, message)
        return True

    async def handle_message(self, event: str, message: qqbot.Message):
        """
        定义事件回调的处理
        :param event: 事件类型
        :param message: 事件对象（如监听消息是Message对象）
        """

        await self.process_commands(event, message)
