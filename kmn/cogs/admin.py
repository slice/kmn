import asyncio
import logging
from io import BytesIO

import asyncpg
import datetime
import discord
from discord import File, User, Embed, Color
from discord.ext.commands import command, group

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.formatting import codeblock, describe as D, KmnEmbed
from kmn.utils import Timer, Table, plural
from kmn.bot import BLOCKED_KEY

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

    @command(hidden=True)
    @is_bot_admin()
    async def shell(self, ctx, *, cmd):
        """run something in bash"""
        result = await shell(cmd)
        await ctx.send(codeblock(result))

    @command(hidden=True)
    @is_bot_admin()
    async def promote(self, ctx, *, who: User):
        """make someone global admin (danger!!)"""
        self.bot.config['admins'].append(who.id)
        await self.bot.save_config()
        await ctx.send(f'\N{OK HAND SIGN} made {who} a global admin.')

    async def flush_blocked_status(self, user: User):
        with await self.bot.redis as conn:
            log.info('flushing blocked status for %d', user.id)
            await conn.delete(BLOCKED_KEY.format(user))

    @group(hidden=True, invoke_without_command=True)
    @is_bot_admin()
    async def block(self, ctx, who: User, *, reason=None):
        """blocks someone from me"""
        query = """
            INSERT INTO blocked_users (user_id, block_reason, blocked_by, blocked_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET block_reason = $2
        """
        await ctx.bot.postgres.execute(
            query,
            who.id, reason, ctx.author.id, datetime.datetime.utcnow()
        )

        await self.flush_blocked_status(who)
        await ctx.send(f'\N{OK HAND SIGN} blocked {D(who)}.')

    @block.command(name='info')
    @is_bot_admin()
    async def block_info(self, ctx, who: User):
        """views block info"""
        query = """
            SELECT * FROM blocked_users
            WHERE user_id = $1
        """
        row = await ctx.bot.postgres.fetchrow(query, who.id)

        if not row:
            return await ctx.send("that user isn't blocked.")

        blocker = ctx.bot.get_user(row['blocked_by'])
        blocker = D(blocker) if blocker else '`<unknown user>`'

        em = KmnEmbed(title=D(who), color=Color.red())
        em.add_fields(
            ('admin', blocker),
            ('reason', row['block_reason'] or '`<no reason>`'),
            inline=False
        )
        await ctx.send(embed=em)

    @command(hidden=True)
    @is_bot_admin()
    async def unblock(self, ctx, who: discord.User):
        """unblocks someone from me"""
        query = """
            DELETE FROM blocked_users
            WHERE user_id = $1
        """
        await ctx.bot.postgres.execute(query, who.id)

        await self.flush_blocked_status(who)
        await ctx.send(f'\N{OK HAND SIGN} unblocked {D(who)}.')

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
