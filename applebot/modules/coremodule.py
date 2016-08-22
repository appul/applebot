import logging

import discord

from applebot.botmodule import BotModule

log = logging.getLogger(__name__)


class CoreModule(BotModule):
    @BotModule.event('message')
    async def on_message(self, message):
        assert isinstance(message, discord.Message)
        # await self.client.commands.parse_message(message)
