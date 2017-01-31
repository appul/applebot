import urllib.parse

import discord

from applebot.module import Module


class LmgtfyModule(Module):
    @Module.Command('lmgtfy')
    async def on_lmgtfy_command(self, message: discord.Message):
        query = message.content[8:]
        if query:
            link = 'http://lmgtfy.com/?q={q}'.format(q=urllib.parse.quote_plus(query))
            await self.client.send_message(message.channel, link)
