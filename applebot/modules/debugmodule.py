import datetime
import logging

import discord

from applebot.module import Module

log = logging.getLogger(__name__)


class DebugModule(Module):
    def __init__(self, *, client, events, commands, config):
        super().__init__(client=client, events=events, commands=commands, config=config)
        assert isinstance(self.client, discord.Client)

    @Module.Command()
    async def on_command_test(self, message):
        assert isinstance(message, discord.Message)
        assert isinstance(self.client, discord.Client)
        await self.client.send_message(message.channel, 'Test: success!')

    @Module.Event()
    async def on_ready(self):
        log.debug('Client: ready')

    @Module.Event()
    async def on_resumed(self):
        log.debug('Client: resumed')

    @Module.Event()
    async def on_message(self, message):
        assert isinstance(message, discord.Message)

    @Module.Event()
    async def on_message_edit(self, message_before, message_after):
        assert isinstance(message_before, discord.Message)
        assert isinstance(message_after, discord.Message)

    @Module.Event()
    async def on_message_delete(self, message):
        assert isinstance(message, discord.Message)

    @Module.Event()
    async def on_typing(self, channel, user, when):
        assert isinstance(channel, (discord.Channel, discord.PrivateChannel))
        assert isinstance(user, (discord.User, discord.Member))
        assert isinstance(when, datetime.datetime)

    @Module.Event()
    async def on_channel_create(self, channel):
        assert isinstance(channel, (discord.Channel, discord.PrivateChannel))

    @Module.Event()
    async def on_channel_delete(self, channel):
        assert isinstance(channel, (discord.Channel, discord.PrivateChannel))

    @Module.Event()
    async def on_channel_update(self, channel_before, channel_after):
        assert isinstance(channel_before, (discord.Channel, discord.PrivateChannel))
        assert isinstance(channel_after, (discord.Channel, discord.PrivateChannel))

    @Module.Event()
    async def on_member_create(self, member):
        assert isinstance(member, discord.Member)

    @Module.Event()
    async def on_member_delete(self, member):
        assert isinstance(member, discord.Member)

    @Module.Event()
    async def on_member_update(self, member_before, member_after):
        assert isinstance(member_before, discord.Member)
        assert isinstance(member_after, discord.Member)

    @Module.Event()
    async def on_member_ban(self, member):
        assert isinstance(member, discord.Member)

    @Module.Event()
    async def on_member_unban(self, server, user):
        assert isinstance(server, discord.Server)
        assert isinstance(user, discord.User)

    @Module.Event()
    async def on_group_join(self, channel, user):
        assert isinstance(channel, (discord.Channel, discord.PrivateChannel))
        assert isinstance(user, discord.User)

    @Module.Event()
    async def on_group_remove(self, channel, user):
        assert isinstance(channel, (discord.Channel, discord.PrivateChannel))
        assert isinstance(user, discord.User)

    @Module.Event()
    async def on_server_join(self, server):
        assert isinstance(server, discord.Server)

    @Module.Event()
    async def on_server_remove(self, server):
        assert isinstance(server, discord.Server)

    @Module.Event()
    async def on_server_update(self, server_before, server_after):
        assert isinstance(server_before, discord.Server)
        assert isinstance(server_after, discord.Server)

    @Module.Event()
    async def on_server_available(self, server):
        assert isinstance(server, discord.Server)

    @Module.Event()
    async def on_server_unavailable(self, server):
        assert isinstance(server, discord.Server)

    @Module.Event()
    async def on_server_role_create(self, role):
        assert isinstance(role, discord.Role)

    @Module.Event()
    async def on_server_role_delete(self, role):
        assert isinstance(role, discord.Role)

    @Module.Event()
    async def on_server_role_update(self, role_before, role_after):
        assert isinstance(role_before, discord.Role)
        assert isinstance(role_after, discord.Role)

    # discord.Emoji???
    # @BotModuleBase.eventhandler('server_emojis_update')
    # async def on_server_emojis_update(self, emoji_before, emoji_after):
    #     assert isinstance(emoji_before, discord.Emoji)
    #     assert isinstance(emoji_after, discord.Emoji)

    @Module.Event()
    async def on_voice_state_update(self, member_before, member_after):
        assert isinstance(member_before, discord.Member)
        assert isinstance(member_after, discord.Member)

        # Can't really assert atm, too many variances, need to go detective mode later o_o
        # @BotModuleBase.eventhandler('socket_raw_receive')
        # async def on_socket_raw_receive(self, msg):
        #     assert isinstance(msg, (str, bytes))
        #
        # @BotModuleBase.eventhandler('socket_raw_send')
        # async def on_socket_raw_send(self, payload=None):
        #     assert payload is None or isinstance(payload, (str, bytes))
