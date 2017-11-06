import json
import logging
import traceback
from pathlib import Path

import aioredis
import asyncpg
from discord import Message, Guild
from discord.ext.commands import Bot as DiscordBot, when_mentioned_or, errors

from kmn.context import Context
from kmn.errors import CommandFailure
from kmn.formatter import Formatter
from kmn.storage import JSONStorage

log = logging.getLogger(__name__)
DESCRIPTION = """a super neat bot by slice#4274"""
BLOCKED_KEY = 'kmn:core:cache:blocked:{0.id}'
PREFIXES_KEY = 'kmn:core:prefixes:{0.id}'


async def prefix_handler(bot: 'Bot', msg: Message):
    await bot.wait_until_ready()

    default_prefixes = bot.config.get('prefixes', ['k?'])
    mention_prefixes = [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']

    if not msg.guild:
        return default_prefixes + mention_prefixes

    prefixes = await bot.get_prefixes_for(msg.guild)
    return mention_prefixes + prefixes


class Bot(DiscordBot):
    def __init__(self, *, config, postgres, redis):
        super().__init__(
            command_prefix=prefix_handler,
            pm_help=None,
            formatter=Formatter(),
            description=DESCRIPTION
        )

        # whoops, my hand slipped
        self.all_commands['help'].help = 'shows some help'

        # store config
        self.config = config

        # blocked users
        self.blocked = JSONStorage('_blocked.json', loop=self.loop)

        # postgres pool
        self.postgres = postgres
        self.redis = redis

        # load all cogs
        log.info('initial cog load')
        self.load_all_cogs()

    async def get_prefixes_for(self, guild: Guild):
        key = PREFIXES_KEY.format(guild)

        with await self.redis as conn:
            if not await conn.exists(key):
                await conn.sadd(key, 'k!', 'k?')
            return await conn.smembers(key, encoding='utf-8')

    def load_all_cogs(self):
        exclude = {'__init__', '__pycache__'} | set(self.config.get('exclude_cogs', []))
        cog_path = Path(__file__).parent / 'cogs'
        cogs = {cog.stem for cog in cog_path.iterdir() if cog.stem not in exclude}
        for cog in cogs:
            log.info('initial load: kmn.cogs.%s', cog)
            self.load_extension(f'kmn.cogs.{cog}')

    @property
    def testing(self):
        return self.config.get('environment', 'production') == 'testing'

    async def save_config(self):
        with open('config.json', 'w') as fp:
            json.dump(self.config, fp, indent=2)
        log.info('saved configuration')

    async def on_ready(self):
        log.info('logged in as %s (%d)', self.user, self.user.id)

    async def is_blocked(self, user):
        # grab cached value
        with await self.redis as conn:
            value = await conn.get(BLOCKED_KEY.format(user))

        # value was cached
        if value is not None:
            return value.decode() == 'yes'

        # grab their blocked status from the database
        query = """
            SELECT * FROM blocked_users
            WHERE user_id = $1
        """
        record = await self.postgres.fetchrow(query, user.id)

        # cache the blocked value in redis
        with await self.redis as conn:
            await conn.set(
                BLOCKED_KEY.format(user),
                'no' if record is None else 'yes',
                expire=600  # 10 minutes
            )

        return record is not None

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return

        # ignore blocked users
        if await self.is_blocked(message.author):
            return

        # invoke context
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        if isinstance(error, errors.UserInputError):
            await ctx.send(f'input error: {error}')
        elif isinstance(error, errors.BotMissingPermissions) or isinstance(error, errors.MissingPermissions):
            await ctx.send("uhh... " + str(error).lower())
        elif isinstance(error, errors.CheckFailure):
            await ctx.send("you can't do that.")
        elif isinstance(error, errors.NoPrivateMessage):
            await ctx.send("you can't do that in a direct message.")
        elif isinstance(error, errors.CommandInvokeError):
            if isinstance(error.original, CommandFailure):
                message = str(error.original).format(prefix=ctx.prefix)
                return await ctx.send(message)

            formatted_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__, limit=7))
            log.fatal('Command invoke error: %s', formatted_traceback)
            await ctx.send('a fatal error has occurred.')
