from applebot.bot import Bot
from applebot.modules.debugmodule import DebugModule


def run():
    bot = Bot(config='example')
    bot.add(DebugModule)
    bot.run()
    return bot


if __name__ == '__main__':
    run()
