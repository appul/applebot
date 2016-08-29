import logging
from types import MethodType
from typing import Tuple

import discord

from applebot.events import Event
from applebot.events import EventManager
from applebot.utils import caller_attr

log = logging.getLogger(__name__)


class HandlerDecorator(object):
    _manager_attribute = None  # type: str

    def __init__(self, *names):
        if not self._manager_attribute:
            raise NotImplementedError('HandlerDecorator needs to be subclassed, with the _manager_attribute class attribute implemented.')

        self.names = names  # type: Tuple[str]

    def __call__(self, function):
        def client_init(method, client):
            manager = getattr(client, self._manager_attribute)  # type: EventManager
            for name in self.names:  # type: str
                event = manager.add(name)  # type: Event
                event.add(method)

        setattr(function, '__client_init__', MethodType(client_init, function))
        return function


class Module(object):
    def __init__(self, client=None):
        self.__name__ = None
        self.client = client or caller_attr('client', levels=3) or discord.Client()
        self.__register_handlers()

    def __register_handlers(self):
        for method in filter(callable, [getattr(self, m) for m in dir(self) if '__' not in m]):
            commands = method.__dict__.get('command_names', ())
            for command in commands:
                log.debug('Adding command \'{}\' in {}'.format(commands, self.__class__.__name__))
                self.client.commands.add(str(command), method)

            events = method.__dict__.get('event_names', ())
            for event in events:
                log.debug('Registering event \'{}\' from {}'.format(event, self.__class__.__name__))
                self.client.events.add(event, method)

    @staticmethod
    def event(*events):
        def inner_decorator(method):
            method.event_names = events
            return method

        return inner_decorator

    @staticmethod
    def command(*commands):
        def inner_decorator(method):
            method.command_names = commands
            return method

        return inner_decorator

    def client_init(self):
        for name in dir(self):
            method = getattr(self, name, None)
            if '__client_init__' in dir(method):
                method.__client_init__()

    class Event(HandlerDecorator):
        _manager_attribute = 'events'

        def __init__(self, *events):
            super().__init__(*events)

    class Command(HandlerDecorator):
        _manager_attribute = 'commands'

        def __init__(self, *commands):
            super().__init__(*commands)
