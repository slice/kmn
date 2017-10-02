import discord
from discord.ext.commands import command

from kmn.cog import Cog

RIGGED = [
    (162819866682851329, 138428648901312512)
]


class Fun(Cog):
    @command()
    async def ship(self, ctx, a: discord.User, b: discord.User):
        """ships two peeps to see their score"""

        a_score, b_score = int(str(a.id)[4]), int(str(b.id)[4])
        score = (a_score + b_score) / 18

        if (a.id, b.id) in RIGGED:
            score = 1.0

        percentage = f'{round(score * 100, 2)}%'

        if score == 0.0:
            message = ':put_litter_in_its_place: never meant to be.'
        elif 0.0 <= score < 0.3:
            message = ':nauseated_face: terrible.'
        elif 0.3 <= score < 0.5:
            message = ':thinking: maybe...'
        elif 0.5 <= score < 0.7:
            message = ':blue_heart: okay i guess :blue_heart: '
        elif 0.7 <= score < 0.8:
            message = ':heart: great match! :heart:'
        elif 0.8 <= score < 0.9:
            message = ':heart: mmm :sweat_drops:'
        elif score >= 0.9:
            message = ':heart: a match made in heaven~ :sweat_drops::heart:'

        await ctx.send(f'{a} x {b}: **{percentage}**, {message}')


def setup(bot):
    bot.add_cog(Fun(bot))