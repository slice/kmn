import logging
from time import monotonic

import discord
from discord import Embed, Color
from discord.ext.commands import command, cooldown, BucketType

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.formatting import format_list
from kmn.utils import timed

log = logging.getLogger(__name__)


class Admin(Cog):
    @command()
    @is_bot_admin()
    async def die(self, ctx):
        """kills me"""
        await ctx.send('ok, bye.')
        await ctx.bot.logout()

    @command()
    async def about(self, ctx):
        """about me!"""
        embed = Embed(title=str(self.bot.user), color=Color.blurple(), description="i'm a cool bot")
        admins = format_list(self.bot.config.get('admins', []), format='<@{item}>')
        embed.add_field(name='admins', value=admins)
        await ctx.send(embed=embed)

    @command(hidden=True)
    @is_bot_admin()
    async def promote(self, ctx, *, who: discord.User):
        """make someone global admin (danger!!)"""
        self.bot.config['admins'].append(who.id)
        await self.bot.save_config()
        await ctx.send(f'\N{OK HAND SIGN} made {who} a global admin.')

    @command(hidden=True)
    @cooldown(rate=1, per=2, type=BucketType.user)
    async def ping(self, ctx):
        """pong"""
        before = monotonic()
        message = await ctx.send('po—')
        after = monotonic()
        await message.edit(content=f'pong! `{round((after - before) * 1000, 2)}ms`')

    @command(hidden=True)
    @is_bot_admin()
    async def block(self, ctx, who: discord.User):
        """blocks someone"""
        await ctx.bot.blocked.put(str(who.id), True)
        await ctx.send(f'\N{OK HAND SIGN} blocked {who}.')

    @command(hidden=True)
    @is_bot_admin()
    async def unblock(self, ctx, who: discord.User):
        """unblocks someone"""
        try:
            await ctx.bot.blocked.delete(str(who.id))
        except KeyError:
            pass
        await ctx.send(f'\N{OK HAND SIGN} unblocked {who}.')

    @command()
    @is_bot_admin()
    async def reload(self, ctx):
        """reloads all extensions"""
        progress = await ctx.send('reloading...')

        with timed() as t:
            for name, ext in ctx.bot.extensions.copy().items():
                try:
                    ctx.bot.unload_extension(name)
                    ctx.bot.load_extension(name)
                except Exception:
                    log.exception('Failed to load %s:', name)
                    return await progress.edit(content=f'failed to load `{name}`.')
        await progress.edit(content=f'reloaded in `{round(t.interval, 2)}ms`.')


def setup(bot):
    bot.add_cog(Admin(bot))
