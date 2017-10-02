import datetime
import functools

import discord
import whois
import whois.parser
from discord.ext.commands import command
from discord import Embed, Color

from kmn.cog import Cog


class Utilities(Cog):
    @command()
    async def whois(self, ctx, *, domain):
        """runs a whois on a domain"""

        pick = lambda l: l[0] if isinstance(l, list) else l

        try:
            info = await self.bot.loop.run_in_executor(None, whois.whois, domain)
        except Exception as exception:
            return await ctx.send(f'failed to whois: `{exception}` \N{THINKING FACE}')

        if not info.get('domain_name'):
            return await ctx.send('domain not found. \N{THINKING FACE}')

        embed = Embed(title=pick(info['domain_name']).lower(), color=Color.blurple())

        # grab registrar
        registrar = pick(info.get('registrar', 'unknown registrar')).lower()

        if registrar == 'enom, inc.':
            registrar += ' (namecheap)'

        embed.add_field(name='registrar', value=registrar)

        def add_date_field(*, key, name):
            time = info.get(key)

            # skip if value was none
            if time is None:
                return

            # pick first in list
            time = pick(time)

            assert isinstance(time, datetime.datetime)

            time = time.strftime('%Y-%m-%d %H:%m')
            embed.add_field(name=name, value=time)

        add_date_field(key='creation_date', name='registered')
        add_date_field(key='expiration_date', name='expires')

        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Utilities(bot))
