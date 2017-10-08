import asyncio
import logging
from io import BytesIO
from time import monotonic

import asyncpg
import discord
from discord import Embed, Color, File
from discord.ext.commands import command, cooldown, BucketType

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.formatting import format_list, codeblock
from kmn.utils import Timer, Table, plural

log = logging.getLogger(__name__)


async def shell(command):
    shell = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    results = await shell.communicate()
    return ''.join(x.decode('utf-8') for x in results)


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
        description = "i'm a cool bot" + (' (testing)' if ctx.bot.testing else '')
        embed = Embed(title=str(self.bot.user), color=Color.blurple(), description=description)
        admins = format_list(self.bot.config.get('admins', []), format='<@{item}>')
        embed.add_field(name='admins', value=admins)
        await ctx.send(embed=embed)

    @command(hidden=True)
    @is_bot_admin()
    async def shell(self, ctx, *, command):
        """run something in bash"""
        result = await shell(command)
        await ctx.send(codeblock(result))

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

    @command(hidden=True)
    @is_bot_admin()
    async def sql(self, ctx, *, sql):
        """execute some sql"""
        # from mousey: https://git.io/vdzge

        # this is probably not the ideal solution...
        if 'select' in sql.lower():
            coro = ctx.bot.postgres.fetch
        else:
            coro = ctx.bot.postgres.execute

        try:
            with Timer() as t:
                result = await coro(sql)
        except asyncpg.PostgresError as e:
            return await ctx.send(f'\N{CACTUS} Failed to execute! {type(e).__name__}: {e}')

        # execute returns the status as a string
        if isinstance(result, str):
            return await ctx.send(f'```\n{result}```\n*took `{t.duration:.2f}ms`*')

        if not result:
            return await ctx.send(f'no results, took `{t.duration:.2f}ms`.')

        # render output of statement
        columns = list(result[0].keys())
        table = Table(*columns)

        for row in result:
            values = [str(x) for x in row]
            table.add_row(*values)

        # properly emulate the psql console
        rows = plural(row=len(result))

        content = f'```\n{table.rendered}```\n*{rows}, took {t.duration:.2f}ms*'
        if len(content) > 2000:
            raw_content = f'{table.rendered}\n{"=" * 140}\n{rows}, took {t.duration:.2f}ms to generate.'
            with BytesIO() as bio:
                bio.write(raw_content.encode())
                bio.seek(0)
                await ctx.send('content was too long.', file=File(bio, 'result.txt'))
        else:
            await ctx.send(content)

    @command()
    @is_bot_admin()
    async def reload(self, ctx):
        """reloads all extensions"""
        progress = await ctx.send('reloading...')

        with Timer() as t:
            for name, ext in ctx.bot.extensions.copy().items():
                try:
                    ctx.bot.unload_extension(name)
                    ctx.bot.load_extension(name)
                except Exception:
                    log.exception('Failed to load %s:', name)
                    return await progress.edit(content=f'failed to load `{name}`.')
        await progress.edit(content=f'reloaded in `{round(t.duration, 2)}ms`.')


def setup(bot):
    bot.add_cog(Admin(bot))
