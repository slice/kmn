from time import monotonic

from discord.ext.commands import command, cooldown, BucketType

from kmn.cog import Cog
from kmn.utils import Timer


class Health(Cog):
    @command(hidden=True, aliases=['p'])
    @cooldown(rate=1, per=2, type=BucketType.user)
    async def ping(self, ctx):
        """pong"""
        with Timer() as timer:
            message = await ctx.send('po—')
        await message.edit(content=f'pong! `{timer}`')


def setup(bot):
    bot.add_cog(Health(bot))
