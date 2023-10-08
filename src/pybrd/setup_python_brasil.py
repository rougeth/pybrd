from pathlib import Path
from loguru import logger
from eventbrite.provider import EventbriteAuthenticationProvider

from pybrd import config
from discord.ext.commands import Bot
from discord import utils

from pybrd.auth.cog import AuthenticationCog


async def setup(bot: Bot):
    logger.info("Getting Discord server")
    guild = await bot.fetch_guild(config.DISCORD_SERVER_ID)
    roles = await guild.fetch_roles()

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
            "src/pybr2023/templates",
        )
    )

    # eventbrite = EventBrite(config.EVENTBRITE_EVENT_ID, config.EVENTBRITE_TOKEN)

    # logger.info("Setup AttendeesIndex")
    # attendees_index = AttendeesIndex(
    #     config.ATTENDEES_CACHE_PATH, config.ATTENDEES_CACHE_ENABLED
    # )

    # logger.info("Setup TalksCog")
    # pretalx = Pretalx(config.PRETALX_EVENT_SLUT, config.PRETALX_TOKEN)
    # await bot.add_cog(TalksCog(bot, guild, pretalx))

    # logger.info("Setup MessageCog")
    # await bot.add_cog(MessagesCog(bot, guild, config.DISCORD_WELCOME_CHANNEL))

    # logger.info("Setup AuthenticationCog")
    # await bot.add_cog(
    #     AuthenticationCog(
    #         bot,
    #         guild,
    #         eventbrite,
    #         attendees_index,
    #         config.DISCORD_ATTENTEE_ROLE_NAME,
    #     )
    # )
