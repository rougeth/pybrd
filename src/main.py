from discord import Intents

from pybrd.bot import Bot
from pybrd import config


bot = Bot(command_prefix="!", intents=Intents.all())

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
