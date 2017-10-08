import json
import logging
import traceback
from pathlib import Path

import aioredis
import asyncpg
from discord.ext.commands import Bot as DiscordBot, when_mentioned_or, errors

from kmn.context import Context
from kmn.errors import CommandFailure
from kmn.formatter import Formatter
from kmn.storage import JSONStorage

log = logging.getLogger(__name__)
DESCRIPTION = """a super neat bot by slice#4274"""


class Bot(DiscordBot):
    def __init__(self, *, config):
        prefixes = config.get('prefixes', ['k~', 'k!'])

        super().__init__(
            command_prefix=when_mentioned_or(*prefixes),
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
        log.info('connecting to postgres')
        _pool_future = asyncpg.create_pool(**config['postgres'])
        self.postgres = self.loop.run_until_complete(_pool_future)

        # redis pool
        log.info('connecting to redis')
        _redis_future = aioredis.create_pool(
            (config['redis']['host'], config['redis']['port']),
            db=config['redis'].get('db', 0)
        )
        self.redis = self.loop.run_until_complete(_redis_future)

        # load all cogs
        log.info('initial cog load')
        self.load_all_cogs()

    def load_all_cogs(self):
        cog_path = Path(__file__).parent / 'cogs'
        cogs = {cog.stem for cog in cog_path.iterdir() if cog.stem not in {'__init__', '__pycache__'}}
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

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return

        # ignore blocked users
        if self.blocked.get(str(message.author.id)):
            return

        # invoke context
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        if isinstance(error, errors.UserInputError):
            await ctx.send(f'input error: {error}')
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
