from time import monotonic

from discord.ext.commands import command, cooldown, BucketType

from kmn.cog import Cog


class Health(Cog):
    @command(hidden=True, aliases=['p'])
    @cooldown(rate=1, per=2, type=BucketType.user)
    async def ping(self, ctx):
        """pong"""
        before = monotonic()
        message = await ctx.send('po—')
        after = monotonic()
        await message.edit(content=f'pong! `{round((after - before) * 1000, 2)}ms`')


def setup(bot):
    bot.add_cog(Health(bot))
