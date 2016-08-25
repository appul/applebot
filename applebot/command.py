import logging

import discord

from applebot.asyncevents import EventManager, Event, EventHandler, CombinedEvent
from applebot.botmodule import BotModule
from applebot.exceptions import BlockCommandException

log = logging.getLogger(__name__)


class CommandModule(BotModule):
    def __init__(self):
        super().__init__()

    @BotModule.event('message')
    async def parse_message(self, message):
        assert isinstance(message, discord.Message)
        if message.author.bot: return
        if message.content[:1] != self.client.config.command_prefix: return
        command_name = message.content[1:].split(' ')[0]
        command = self.client.commands.get(command_name)
        log.debug('Received command: {}'.format(command_name))
        await self.emit_command(command, message)

    async def emit_command(self, command, message):
        if command:
            try: await self.client.events.emit('command_received', message, command)
            except BlockCommandException as e:
                await self.client.events.emit('command_blocked', message, command, e)
            else: await command.emit(message)
        else:
            log.debug('Command not registered')
            await self.client.events.emit('command_notfound', message, command)
        await self.client.events.emit('command_finished', message, command)

    @BotModule.event('command_received')
    async def on_command_receive(self, message, command):
        if message.author.id == self.client.config.owner: return

        if not command.private and message.channel.is_private:
            log.debug('Command blocked, reason: not allowed in private channels')
            raise BlockCommandException('not allowed in private')

        if not command.public and not message.channel.is_private:
            log.debug('Command blocked, reason: not allowed in public channels')
            raise BlockCommandException('not allowed in public')

    @BotModule.command('help')
    async def on_help_command(self, message):
        """!help <command> | Get help for a command."""
        assert isinstance(message, discord.Message)
        command_arg = message.content[6:]
        command_help = self.client.commands.get(command_arg).help
        if command_help is None:
            return await self.client.send_message(message.channel, 'Could not find help for command `{}`'.format(command_arg))
        return await self.client.send_message(message.channel, 'Help for command `{}`:\n{}'.format(command_arg, command_help))


class CommandManager(EventManager):
    def __init__(self):
        super().__init__()
        self.__dict__['_event_type'] = Command


class Command(Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.public = True  # type: bool
        self.private = True  # type: bool
        self._handler_type = Callback
        self._combined_type = CombinedCommand

    @property
    def help(self):
        handler_helps = [h.help for h in self if h.help is not None]
        if handler_helps:
            return '\n'.join(handler_helps)
        return None


class CombinedCommand(CombinedEvent):
    pass


class Callback(EventHandler):
    @property
    def help(self):
        return self.handler.__doc__
