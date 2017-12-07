import inspect
import traceback

import datetime
from discord import Guild, Message, Embed, Color
from discord.ext.commands import errors, command
from discord.utils import maybe_coroutine

from kmn.bot import Bot
from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.context import Context
from kmn.errors import CommandFailure


def trace(error: Exception) -> str:
    return ''.join(traceback.format_exception(type(error), error, error.__traceback__, limit=7))


class Reporting(Cog):
    async def broadcast(self, stream: str, *args, **kwargs) -> Message:
        """
        Broadcasts a message to a channel specified in the configuration file.

        Parameters
        ----------
        stream : str
            The name of the stream to broadcast to.

        Returns
        -------
        discord.Message
            The sent message, if any.

        Raises
        ------
        discord.HTTPException
            If an error occurs broadcasting the message.
        """
        channel = self.bot.get_channel(self.bot.config['streams'][stream])

        if not channel:
            raise RuntimeError('Stream channel %s was not found.', stream)

        return await channel.send(*args, **kwargs)

    async def on_command_error(self, ctx: Context, error: Exception):
        # Matcher : { Class | Set<Class> }
        # Handler : String | Coroutine | Function<P1=Exception, RET=String>
        # Handlers : Dict<K=Matcher, V=Handler>
        handlers = {
            errors.UserInputError: 'input error: {error}',
            (errors.MissingPermissions, errors.BotMissingPermissions): lambda error: f'uhh... {str(error).lower()}',
            errors.CheckFailure: "you can't do that.",
            errors.NoPrivateMessage: "you can't do that in a dm."
        }

        for matcher, handler in handlers.items():
            matcher_set_satisfied = \
                isinstance(matcher, tuple) and any(type(error) is item for item in matcher)
            singular_match_satisfied = \
                inspect.isclass(matcher) and type(error) is matcher

            if not matcher_set_satisfied and not singular_match_satisfied:
                continue

            if isinstance(handler, str):
                # simple string send sending
                await ctx.send(handler.format(error=error))
                return
            elif callable(handler):
                # send callable return
                await ctx.send(await maybe_coroutine(handler, error))
            else:
                raise TypeError(f'Unknown error handler type: {handler}')

        if isinstance(error, errors.CommandInvokeError):
            # :class:`CommandFailure`s should be handled specifically.
            if isinstance(error.original, CommandFailure):
                message = str(error.original).format(prefix=ctx.prefix)
                await ctx.send(message)
                return

            await ctx.send('a fatal error has occurred.')

            embed = Embed(title='fatal error', description=f'```py\n{trace(error.original)}\n```', color=Color.red())
            embed.add_field(name='invoker', value=f'{ctx.author} `{ctx.author.id}`')
            embed.set_footer(text=datetime.datetime.utcnow())

            if ctx.guild:
                embed.add_field(name='guild', value=f'{ctx.guild.name} `{ctx.guild.id}`')

            await self.broadcast('errors', embed=embed)

    async def on_guild_join(self, guild: Guild):
        await self.broadcast('guilds', f'\N{LARGE BLUE CIRCLE} {guild.name} `{guild.id}`')

    async def on_guild_remove(self, guild: Guild):
        await self.broadcast('guilds', f'\N{LARGE RED CIRCLE} {guild.name} `{guild.id}`')

    @command(hidden=True)
    @is_bot_admin()
    async def __raise(self, ctx: Context, *, message):
        """raise an error for debugging purposes"""
        raise RuntimeError(message)


def setup(bot: Bot):
    bot.add_cog(Reporting(bot))
