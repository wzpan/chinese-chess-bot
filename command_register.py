#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
command_register: 用于指令注册

author: wzpan
email: m@hahack.com
"""


import qqbot


def command(command_str: str, validate_func=None, invalid_func=None):
    """
    指令的装饰器
    :param command_str: 指令的字符串。例如 `/菜单`
    :param check_param: 是否需要检查参数
    :param invalid_func: 当参数不符合要求时的处理函数
    :return: 装饰器
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if command_str != "" and command_str in args[2].content:
                # 指令字符串不为空，并且指令匹配成功
                qqbot.logger.info("command %s" % command_str)
                # 解析去除指令之后剩下的参数字符串
                params = args[2].content.split(command_str)[1].strip()
                if validate_func and not validate_func(params):
                    # 如果需要检查参数，并且参数为空
                    # 调用 invalid_func 函数
                    return await invalid_func(args[1], args[2])
                # 调用被装饰的处理函数
                return await func(params, args[1], args[2])
            else:
                qqbot.logger.debug("skip command %s" % command_str)
                # 指令不匹配，跳过
                return None

        return wrapper

    return decorator
