import logging
from typing import Dict
from typing import Union

import discord

from applebot.config import Config
from applebot.exceptions import BlockCommandError
from applebot.module import Module

log = logging.getLogger(__name__)


class CommandModule(Module):
    def __init__(self, prefix='!', *, client, events, commands, config):
        super().__init__(client=client, events=events, commands=commands, config=config)
        self.prefix = prefix
        self._configs = {}  # type: Dict[str, 'CommandConfig']
        self._setup_configs()

    def _setup_configs(self):
        if self.config:
            for name, config in self.config.items():
                self._configs[name] = CommandConfig(config)

    @Module.Event('message')
    async def parse_message(self, message):
        assert isinstance(message, discord.Message)
        if message.author.bot: return
        if message.content[:1] != self.prefix: return
        command_name = message.content[1:].split(' ')[0]
        command = self.commands.get(command_name)
        log.debug('Received command: {}'.format(command_name))
        await self.emit_command(command, message, command_name)

    async def emit_command(self, command, message, command_name):
        if command:
            try: await self.events.emit('command_received', message, command)
            except BlockCommandError as e:
                await self.events.emit('command_blocked', message, command, e)
            else: await command.emit(message)
        else:
            log.debug('Command not registered')
            await self.events.emit('command_notfound', message, command_name)
        await self.events.emit('command_finished', message, command or command_name)

    @Module.Event('command_received')
    async def on_command_receive(self, message, command):
        # if message.author.id == self.client.config.owner: return
        if not self._check_command_config(command, message):
            raise BlockCommandError('denied by command config')

    def _check_command_config(self, command, message) -> bool:
        config = self._configs.get(str(command)) or self._configs.get('global')
        if config:
            return config.check(message)
        return True

    @Module.Command('help')
    async def on_help_command(self, message):
        """`!help <command>` | Get help for a command."""
        assert isinstance(message, discord.Message)
        command_arg = message.content[6:] or 'help'
        command = self.commands.get(command_arg)
        if command is None:
            return await self.client.send_message(message.channel, 'Command `{}` does not exist.'.format(command_arg))

        command_help = self._get_command_help(command)
        if command_help is None:
            return await self.client.send_message(message.channel, 'Help for command `{}` doesn\'t exist.'.format(command_arg))
        return await self.client.send_message(message.channel, 'Help for command `{}`:\n{}'.format(command_arg, command_help))

    @staticmethod
    def _get_command_help(command) -> str:
        handler_helps = filter(None, [str(h.handler.__doc__) for h in command])
        if handler_helps:
            return '\n'.join(handler_helps)
        return None


class CommandConfig(Config):
    def __init__(self, config=None):
        super().__init__()
        self.allow = {}  # type: Dict[str, Union[str, int, dict, list]]
        self.deny = {}  # type: Dict[str, Union[str, int, dict, list]]
        if config is not None:
            self.load(config)

    def check(self, message) -> bool:
        def check(msg, cfg):
            log.debug('Check: {}, {}'.format(msg, cfg))
            if msg is None: return False
            if cfg is True: return True
            if isinstance(cfg, dict):
                for key, var in cfg.items():
                    obj = msg.get(key) if isinstance(msg, dict) else getattr(msg, key, None)
                    if check(obj, var):
                        return True
            if isinstance(cfg, (str, str, bool)):
                if str(msg) == str(cfg):
                    return True
            if isinstance(cfg, (list, tuple)):
                if msg in cfg:
                    return True
            return False

        allow = check(message, self.allow) if self.allow else True
        deny = check(message, self.deny) if self.deny else False
        return allow and not deny
