import logging

import discord

from applebot.module import Module

log = logging.getLogger(__name__)


class CoreModule(Module):
    @Module.Event('message')
    async def on_message(self, message):
        assert isinstance(message, discord.Message)
        # await self.client.commands.parse_message(message)
