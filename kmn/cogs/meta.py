from discord import Embed, Color
from discord.ext.commands import command

from kmn.cog import Cog
from kmn.formatting import format_list


class Meta(Cog):
    @command(aliases=['info'], hidden=True)
    async def about(self, ctx):
        """about me!"""
        server_invite = ctx.bot.config.get('server_invite')
        source_code_link = ctx.bot.config.get('source_code_link')

        description = "i'm a cool bot" + (' (testing)' if ctx.bot.testing else '')
        embed = Embed(title=str(self.bot.user), color=Color.blurple(), description=description)
        admins = format_list(self.bot.config.get('admins', []), format='<@{item}>')
        embed.add_field(name='admins', value=admins)

        if server_invite:
            embed.add_field(name='server', value=server_invite)
        if source_code_link:
            embed.add_field(name='source', value=source_code_link)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Meta(bot))
