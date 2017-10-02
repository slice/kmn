import logging
import traceback

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

        self.blocked = JSONStorage('_blocked.json', loop=self.loop)

        # load all cogs
        for cog in self.config.get('cogs', []):
            self.load_extension('kmn.cogs.{}'.format(cog))

    async def on_ready(self):
        log.info('logged in as %s (%d)', self.user, self.user.id)

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return

        if self.blocked.get(str(message.author.id)):
            return

        # invoke context
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        if isinstance(error, errors.UserInputError):
            await ctx.send(f'input error: {str(error).lower()}')
        elif isinstance(error, errors.CheckFailure):
            await ctx.send("you can't do that.")
        elif isinstance(error, errors.NoPrivateMessage):
            await ctx.send("you can't do that in a direct message.")
        elif isinstance(error, errors.CommandInvokeError):
            if isinstance(error.original, CommandFailure):
                message = str(error.original)\
                    .format(prefix=ctx.prefix)
                return await ctx.send(message)

            formatted_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__, limit=7))
            log.fatal('Command invoke error: %s', formatted_traceback)
            await ctx.send('a fatal error has occurred.')
