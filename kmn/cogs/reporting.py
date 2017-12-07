import traceback

import datetime
from discord import Guild, Message, Embed, Color
from discord.ext.commands import errors, command

from kmn.bot import Bot
from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.context import Context
from kmn.errors import CommandFailure


def trace(error: Exception):
    return ''.join(traceback.format_exception(type(error), error, error.__traceback__, limit=7))


class Reporting(Cog):
    async def broadcast(self, stream: str, *args, **kwargs) -> Message:
        channel = self.bot.get_channel(self.bot.config['streams'][stream])

        if not channel:
            raise RuntimeError('Stream channel %s was not found.', stream)

        return await channel.send(*args, **kwargs)

    async def on_command_error(self, ctx: Context, error: Exception):
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
        """raise an error"""
        raise RuntimeError(message)


def setup(bot: Bot):
    bot.add_cog(Reporting(bot))
