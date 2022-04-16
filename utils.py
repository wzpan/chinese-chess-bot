from typing import NoReturn
import qqbot

def is_admin(token: str, guild_id: str, user_id: str) -> NoReturn:
    """
    判断指定用户是否管理员
    
    :param token: token
    :param guild_id: 频道id
    :param user_id: 用户id    
    """
    api = qqbot.GuildMemberAPI(token, False)
    member = api.get_guild_member(guild_id, user_id)
    return any(role in member.roles for role in ("2", "4"))

def search_role(token: str, guild_id: str, role_name: str) -> qqbot.guild_role.Role:
    """
    根据名字查找某个身份组
    
    :param token: token
    :param guild_id: 频道ID
    :param role_name: 身份组名
    :return: 该身份组或者None
    """
    api = qqbot.GuildRoleAPI(token, False)
    guild_roles = api.get_guild_roles(guild_id)
    for role in guild_roles.roles:
        if role.name == role_name:
            return role
    return None

def create_role(token: str, guild_id: str, role_info: qqbot.RoleUpdateInfo) -> NoReturn:
    """
    添加身份组
    
    :param token: token
    :param guild_id: 频道ID
    :param role_info: 要创建的身份组信息
    :return: 是否创建成功
    """
    api = qqbot.GuildRoleAPI(token, False)
    if not search_role(token, guild_id, role_info.name):
        api.create_guild_role(guild_id, role_info)
        
def give_role(token: str, guild_id: str, user_id: str, role_info: qqbot.RoleUpdateInfo) -> bool:
    """
    为指定用户添加身份组
    
    :param token: token
    :param guild_id: 频道ID
    :param role_info: 要创建的身份组信息
    :return: 是否添加成功
    """
    api = qqbot.GuildRoleAPI(token, False)
    # 确保身份组已创建
    create_role(token, guild_id, role_info)
    role = search_role(token, guild_id, role_info.name)
    return api.create_guild_role_member(guild_id, role.id, user_id, None)

async def send_message(token: str, content: str, event: str, message: qqbot.Message) -> NoReturn:
    """
    机器人发送消息
    
    :param content: 发消息的内容
    :param event: 事件名
    :param message: qqbot.Message消息体
    """    
    msg_api = qqbot.AsyncMessageAPI(token, False)
    dms_api = qqbot.AsyncDmsAPI(token, False)

    send = qqbot.MessageSendRequest(content, message.id)
    if event == "DIRECT_MESSAGE_CREATE":
        await dms_api.post_direct_message(message.guild_id, send)
    else:
        await msg_api.post_message(message.channel_id, send)

