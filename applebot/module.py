import logging
from types import MethodType
from typing import Tuple

import discord

from applebot.events import Event
from applebot.events import EventManager

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
    def __init__(self, *, client):
        self.__name__ = None  # type: str
        self.client = client  # type: discord.Client

    def client_init(self):
        for name in dir(self):
            method = getattr(self, name, None)
            if '__client_init__' in dir(method):
                method.__client_init__(self.client)

    class Event(HandlerDecorator):
        _manager_attribute = 'events'

        def __init__(self, *events):
            super().__init__(*events)

    class Command(HandlerDecorator):
        _manager_attribute = 'commands'

        def __init__(self, *commands):
            super().__init__(*commands)
