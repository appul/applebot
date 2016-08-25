import logging

import discord

from applebot.utils import caller_attr

log = logging.getLogger(__name__)


class BotModule(object):
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
