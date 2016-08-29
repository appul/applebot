from applebot.bot import Bot
from applebot.modules.commandmodule import CommandModule
from applebot.modules.logmodule import LogModule


def run():
    bot = Bot()
    bot.setup(config='example')
    bot.add(LogModule)
    bot.add(CommandModule)
    bot.run()
    return bot


if __name__ == '__main__':
    run()
