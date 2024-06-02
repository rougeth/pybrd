import re
from typing import Optional
import discord
from discord.ext import commands, tasks
from discord import utils
from loguru import logger

from pybrd import config
from pybrd.templates import Templates

from .provider import BaseAuthenticationProvider


EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")


def find_email(message: str):
    result = EMAIL_REGEX.search(message)
    if result:
        return result.group()
    return None


class AuthenticationCog(commands.Cog):
    """
    Authentication Cog.

    Tasks:
    - refresh - Execute provider refresh task.

    Commands:
    - auth:refresh - Manually execute provider refresh task.
    - auth:clear_cache - Clean up authentication cache.
    - auth:info - Return authentication stats
    - auth:check - Checks if an email is authorized

    Events:
    - new messages - Listen to private messages and authenticate users.
    """

    def __init__(
        self,
        bot: commands.Bot,
        guild: discord.Guild,
        welcome_channel_id: str,
        auth_provider: BaseAuthenticationProvider,
        attendee_role: discord.Role,
        templates: Templates,
    ):
        self.bot = bot
        self.guild = guild
        self.welcome_channel_id = welcome_channel_id
        self.attendee_role = attendee_role
        self.auth = auth_provider
        self.templates = templates
        # Auth refresh task
        task = tasks.loop(seconds=self.auth.REFRESH_INTERVAL)(
            self.task_refresh_auth_provider
        )
        task.start()

    async def task_refresh_auth_provider(self):
        await self.auth.refresh()

    @commands.command("auth:refresh")
    @commands.has_role(config.PYBR_ORG_ROLE)
    async def refresh(
        self,
        context: commands.Context,
        *args,
    ):
        await self.auth.refresh()
        await context.message.add_reaction("✅")

    @commands.command("auth:clear_cache")
    @commands.has_role(config.PYBR_ORG_ROLE)
    async def clear_cache(
        self,
        context: commands.Context,
        *args,
    ):
        await self.auth.clear_cache()
        await context.message.add_reaction("✅")

    @commands.command("auth:info")
    @commands.has_role(config.PYBR_ORG_ROLE)
    async def info(
        self,
        context: commands.Context,
        *args,
    ):
        stats = await self.auth.stats()
        message = "\n".join(
            [f"- {key.capitalize()}: `{value}`" for key, value in stats.items()]
        )
        await context.reply(f"Auth Info:\n{message}")

    @commands.command("auth:check")
    @commands.has_role(config.PYBR_ORG_ROLE)
    async def check(
        self,
        context: commands.Context,
        email: str,
        *args,
    ):
        email = email.lower()
        if await self.auth.authenticate(email):
            await context.reply(f"✅ Email `{email}` encontrado")
        else:
            await context.reply(f"❌ Email `{email}` **não** encontrado")

    def _is_private_message(self, message: discord.Message) -> bool:
        conditions = (
            not message.author.bot,
            message.channel.type == discord.ChannelType.private,
        )
        return all(conditions)

    async def _get_user_from_server(
        self, user: discord.Member
    ) -> Optional[discord.Member]:
        return await self.guild.fetch_member(user.id)

    def _is_user_authenticated(self, user: discord.Member) -> bool:
        return utils.get(user.roles, id=self.attendee_role.id)

    async def _set_attendee_role(self, member: discord.Member):
        await member.add_roles(self.attendee_role)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listen to private messages and authenticate users.
        Checks if:
            - Message is private from user to bot, if not, ignore
            - User is a member of the server, if not, send information about Python Brasil
            - User is already authenticated, if yes, send link to welcome channel
            - Email is present in message, if not, send information about missing email
            - User is authorized, if yes, authenticate and send link to welcome channel
        """
        if not self._is_private_message(message):
            return

        user = await self._get_user_from_server(message.author)
        if not user:
            reply = self.templates.render(
                "auth_user_not_in_server.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            return

        if self._is_user_authenticated(user):
            reply = self.templates.render(
                "auth_user_authenticated.md",
                user_id=message.author.id,
                welcome_channel_id=self.welcome_channel_id,
            )
            await message.author.send(reply)
            return

        email = find_email(message.content.lower())
        if not email:
            logger.warning(
                f"Email not found in message. author={message.author!r}, message={message.content!r}"
            )
            reply = self.templates.render(
                "auth_email_missing.md",
                user_id=message.author.id,
            )
            await message.author.send(reply)
            # await self._log_auth_failed(message)
            return

        if await self.auth.authenticate(email):
            logger.info(
                f"User authenticated. author={message.author!r}, message={message.content!r}"
            )
            await self._set_attendee_role(user)
            reply = self.templates.render(
                "auth_succeeded.md", welcome_channel_id=self.welcome_channel_id
            )
            await message.author.send(reply)
        else:
            logger.warning(
                f"Failed to authenticate user. author={message.author!r}, message={message.content!r}"
            )
            reply = self.templates.render(
                "auth_failed.md",
                previous_message=message.content,
            )
            await message.author.send(reply)
            # await self._log_auth_failed(message)
