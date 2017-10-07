"""
Custom command context for kmn.

Most of the database-management code was stolen from Danny (@Rapptz on GitHub). Thanks!
"""

import discord
from discord import Color, Embed
from discord.ext.commands import Context as DiscordContext

from kmn.guild_config import GuildConfig


class _ContextDBAcquire:
    __slots__ = ('ctx', 'timeout')

    def __init__(self, ctx, timeout):
        self.ctx = ctx
        self.timeout = timeout

    def __await__(self):
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.ctx._acquire(self.timeout)
        return self.ctx.db

    async def __aexit__(self, *args):
        await self.ctx.release()


class Context(DiscordContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # mirrored from bot
        self.postgres = self.bot.postgres
        self.redis = self.bot.redis

        # guild-specific configuration
        self.config = GuildConfig(self.guild, redis=self.redis)

        # database connection
        self.db = None

    async def ok(self, emoji='\N{OK HAND SIGN}'):
        try:
            await self.message.add_reaction(emoji)
        except:
            await self.send(emoji)

    async def _acquire(self, timeout):
        if self.db is None:
            self.db = await self.postgres.acquire(timeout=timeout)
        return self.db

    def acquire(self, *, timeout=None):
        return _ContextDBAcquire(self, timeout=timeout)

    async def release(self):
        if self.db is not None:
            await self.bot.postgres.release(self.db)
            self.db = None

    async def confirm(self, **kwargs):
        embed = Embed(**kwargs, color=Color.red())

        # send embed
        try:
            message = await self.send(embed=embed)
        except discord.HTTPException:
            return False

        reactions = {
            '\N{WHITE HEAVY CHECK MARK}': True,
            '\N{CROSS MARK}': False
        }

        # add reactions
        for reaction in reactions.keys():
            try:
                await message.add_reaction(reaction)
            except discord.HTTPException:
                return False

        # only accept reactions from the same person and channel
        def _check(added_reaction, user):
            return user == self.author and added_reaction.message.channel == self.channel

        # wait for reaction
        while True:
            reaction, adder = await self.bot.wait_for('reaction_add', check=_check)

            # ignore custom emoji
            if not isinstance(reaction.emoji, str):
                continue

            truth_value = reactions.get(reaction.emoji, None)

            if truth_value is not None:
                await message.delete()
                return truth_value
