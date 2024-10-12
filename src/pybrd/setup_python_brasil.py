from pathlib import Path
from loguru import logger
from pybrd.auth.providers.eventbrite import EventbriteAuthenticationProvider

from pybrd import config
from discord.ext.commands import Bot
from discord import utils

from pybrd.auth.cog import AuthenticationCog
from pybrd.templates import Templates


async def setup(bot: Bot):
    logger.info("Getting Discord server")
    guild = await bot.fetch_guild(config.DISCORD_SERVER_ID)
    roles = await guild.fetch_roles()
    templates = Templates("src/pybr2024/templates")

    logger.info("Setup Authentication Provider")
    attendee_role = utils.get(roles, name=config.AUTH_ATTENDEE_ROLE)
    auth_provider = EventbriteAuthenticationProvider(
        config.EVENTBRITE_EVENT_ID,
        config.EVENTBRITE_API_TOKEN,
        Path(config.AUTH_INDEX_PATH),
        config.AUTH_INDEX_CACHED,
    )

    await bot.add_cog(
        AuthenticationCog(
            bot,
            guild,
            config.PYBR_WELCOME_CHANNEL,
            auth_provider,
            attendee_role,
            templates,
        )
    )
