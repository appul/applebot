import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from unidecode import unidecode

from applebot.module import Module

MAX_LOG_SIZE_BYTES = 1024 * 1024
LOG_BACKUP_COUNT = 5

log = logging.getLogger(__name__)
msg_log = logging.getLogger('on_message')
cmd_log = logging.getLogger('on_command')


class DecodedFormatter(logging.Formatter):
    def format(self, record):
        return unidecode(super().format(record))  # Remove unicode symbols


class LogModule(Module):
    def __init__(self, *, client, events, commands):
        super().__init__(client=client, events=events, commands=commands)
        self.initialize()

    def initialize(self):
        log_formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(module)7s] [%(levelname)5s] %(message)s', '%H:%M:%S')

        log_dir = os.path.join(os.path.dirname(os.path.realpath(sys.modules['__main__'].__file__)), 'log')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        cli_log = logging.StreamHandler()
        cli_log.setFormatter(log_formatter)
        cli_log.setLevel(logging.DEBUG if self.client.config.debug else logging.INFO)

        file_log = RotatingFileHandler(os.path.join(log_dir, 'log.log'), backupCount=LOG_BACKUP_COUNT, maxBytes=MAX_LOG_SIZE_BYTES, encoding='utf-8')
        file_log.setFormatter(log_formatter)
        file_log.setLevel(logging.INFO)

        debug_log = RotatingFileHandler(os.path.join(log_dir, 'debug.log'), backupCount=LOG_BACKUP_COUNT, maxBytes=MAX_LOG_SIZE_BYTES, encoding='utf-8')
        debug_log.setFormatter(log_formatter)
        debug_log.setLevel(logging.DEBUG)

        root_log = logging.getLogger('')
        root_log.addHandler(cli_log)
        root_log.addHandler(file_log)
        root_log.addHandler(debug_log)
        root_log.setLevel(logging.DEBUG)

        messages_formatter = DecodedFormatter('%(asctime)s.%(msecs)03d %(message)s', '%H:%M:%S')
        messages_log = RotatingFileHandler(os.path.join(log_dir, 'messages.log'), backupCount=LOG_BACKUP_COUNT, maxBytes=MAX_LOG_SIZE_BYTES, encoding='utf-8')
        messages_log.setFormatter(messages_formatter)
        messages_log.setLevel(logging.INFO)
        msg_log.addHandler(messages_log)

        commands_formatter = DecodedFormatter('%(asctime)s.%(msecs)03d [%(levelname)5s] %(message)s', '%H:%M:%S')
        commands_log = RotatingFileHandler(os.path.join(log_dir, 'commands.log'), backupCount=LOG_BACKUP_COUNT, maxBytes=MAX_LOG_SIZE_BYTES, encoding='utf-8')
        commands_log.setFormatter(commands_formatter)
        commands_log.setLevel(logging.INFO)
        logging.addLevelName(26, 'Received')
        logging.addLevelName(27, 'Finished')
        logging.addLevelName(28, 'NotFound')
        logging.addLevelName(29, 'Blocked')
        cmd_log.addHandler(commands_log)

    @Module.Event('message')
    async def on_message(self, message):
        msg_log.info('[Ch: {0.channel.name}] [+] {0.author.name}: {0.content}'.format(message))

    @Module.Event('message_delete')
    async def on_message_delete(self, message):
        msg_log.info('[Ch: {0.channel.name}] [-] {0.author.name}: {0.content}'.format(message))

    @Module.Event('message_edit')
    async def on_message_edit(self, before, after):
        msg_log.info('[Ch: {0.channel.name}] [-] {0.author.name}: {0.content}'.format(before))
        msg_log.info('[Ch: {0.channel.name}] [+] {0.author.name}: {0.content}'.format(after))

    @Module.Event('command_received')
    async def on_command_received(self, message, command):
        cmd_log.log(26, '[Ch: {0.channel.name}] {0.author.name}: {1.name} - "{0.content}"'.format(message, command))

    @Module.Event('command_finished')
    async def on_command_finished(self, message, command):
        cmd_log.log(27, '[Ch: {0.channel.name}] {0.author.name}: {1}'.format(message, command))

    @Module.Event('command_notfound')
    async def on_command_notfound(self, message, command):
        cmd_log.log(28, '[Ch: {0.channel.name}] {0.author.name}: {1}'.format(message, command))

    @Module.Event('command_blocked')
    async def on_command_blocked(self, message, command, e):
        cmd_log.log(29, '[Ch: {0.channel.name}] {0.author.name}: {1.name} - {2}'.format(message, command, e))
