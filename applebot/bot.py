import logging
from asyncio import iscoroutinefunction
from typing import Dict

import discord

from applebot.config import Config
from applebot.enums import EVENT
from applebot.events import EventManager
from applebot.module import Module
from applebot.modules.commandmodule import CommandManager
from applebot.utils import call_co

MAX_LOG_SIZE_BYTES = 1024 * 1024
LOG_BACKUP_COUNT = 2

log = logging.getLogger(__name__)


class Bot(discord.Client):
    _module_base_type = Module  # Allow child classes to override the module base

    def __init__(self, *, config=None, **options):
        super().__init__(**options)
        self.config = BotConfig(config)
        self.events = EventManager()
        self.commands = CommandManager()
        self._bot_modules = {}  # type: Dict[str, Module]
        self.initialize()

    def initialize(self):
        self._setup_events()

    def run(self, *args, **kwargs):
        """Run it! Start the bot"""
        if not args and not kwargs:
            if self.config.token:
                return super().run(self.config.token)
            if self.config.username and self.config.password:
                return super().run(self.config.username, self.config.password)
        return super().run(*args, **kwargs)

    def add(self, module_class):
        """Add a module to the bot"""
        if not issubclass(module_class, self._module_base_type):
            raise TypeError('Parameter \'module\' is not of type {0}'.format(self._module_base_type.__name__))
        if module_class.__name__ in self._bot_modules:
            raise LookupError('Module {0.name} has already been added'.format(module_class))
        log.debug('Adding bot module: {0}'.format(module_class.__name__))

        module = module_class(client=self)
        module.client_init()
        self._bot_modules[module_class.__name__] = module

    async def emit(self, *args, **kwargs):
        """Emit an event and call its handlers"""
        await self.events.emit(*args, **kwargs)

    def on(self, event_name, handler):
        """Register an event handler"""
        return self.events.add(event_name, handler)

    def register(self, event_name):
        """Decorator for registering an event handler"""

        def method_decorator(method):
            self.on(event_name, method)
            return method

        return method_decorator

    async def on_error(self, *args, **kwargs):
        log.error(*args, **kwargs)
        await self.events.emit('error', *args, **kwargs)
        await super().on_error(*args, **kwargs)

    #########
    # setup #
    #########
    def _setup_events(self):
        for event in EVENT:
            if event.type > EVENT.TYPE.NONE:
                if event.type < EVENT.TYPE.HTTP_METHOD:
                    self.events.add(str(event))
                    if event.type == EVENT.TYPE.IN:
                        self._attach_emitter(str(event))
                else:
                    self._hook_method(self.http, str(event)[5:], 'http_{m}_request', 'http_{m}_request')
            else:
                self._hook_method(self, str(event))

    def _attach_emitter(self, event):
        async def emitter(*args, **kwargs):
            await self.events.emit(event, *args, **kwargs)

        emitter.__name__ = 'on_{}'.format(event)
        self.event(emitter)

    def _hook_method(self, obj, method_name, event_before='{m}_request', event_after='{m}_response'):
        """Hook a method with before and after events."""
        method = getattr(obj, method_name)
        new_method = self._wrap_method(method, event_before.format(m=method_name), event_after.format(m=method_name))

        setattr(obj, '_unhooked_{}'.format(method_name), method)
        setattr(obj, method_name, new_method)

    def _wrap_method(self, method, before, after):
        if iscoroutinefunction(method):
            async def wrapped_method(*args, **kwargs):
                await self.emit(before, *args, **kwargs)
                result = await method(*args, **kwargs)
                await self.emit(after, result, *args, **kwargs)
                return result

        else:
            def wrapped_method(*args, **kwargs):
                call_co(self.emit(before, *args, **kwargs))
                result = method(*args, **kwargs)
                call_co(self.emit(after, result, *args, **kwargs))
                return result

        return wrapped_method


class BotConfig(Config):
    def __init__(self, *args, **kwargs):
        self.debug = False
        self.command_prefix = '!'
        self.username = None
        self.password = None
        self.token = None
        self.owner = 0
        super().__init__(*args, **kwargs)
