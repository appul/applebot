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
        for method in [getattr(self, m) for m in dir(self) if '__' not in m]:
            if callable(method):
                command = method.__dict__.get('command_name')
                event = method.__dict__.get('event_name')
                if command:
                    log.debug('Adding command \'{}\' in {}'.format(command, self.__class__.__name__))
                    for command in (command if isinstance(command, (tuple, list)) else (command,)):
                        self.client.commands.add(str(command), method)
                if event:
                    log.debug('Registering event \'{}\' from {}'.format(event, self.__class__.__name__))
                    self.client.events.add(event, method)

    @staticmethod
    def event(event):
        def inner_decorator(method):
            method.event_name = str(event)
            return method

        return inner_decorator

    @staticmethod
    def command(command):
        def inner_decorator(method):
            method.command_name = command
            return method

        return inner_decorator
