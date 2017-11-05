import random
import re

import discord
from discord import User, Member
from discord.ext.commands import command, clean_content, cooldown, BucketType

from kmn.cog import Cog
from kmn.context import Context
from kmn.errors import CommandFailure

RIGGED = {
    (162819866682851329, 138428648901312512)
}


class Fun(Cog):
    @command()
    async def pick(self, ctx: Context, *things: clean_content):
        """pick some things"""
        unique_things = set(things)

        if len(unique_things) < 2:
            raise CommandFailure('you need more than 1 unique thing.')

        await ctx.send(random.choice(things))

    @command()
    async def owo(self, ctx: Context, *, text: clean_content):
        """hewwo!!"""

        faces = ["(・`ω´・)", ";;w;;", "owo", "UwU", ">w<", "^w^"]

        replacement_table = {
            r'[rl]': 'w',           r'[RL]': 'W',
            r'n([aeiou])': 'ny\\1', r'N([aeiou])': 'Ny\\1',
            r'ove': 'uv'
        }

        for regex, replace_with in replacement_table.items():
            text = re.sub(regex, replace_with, text)

        await ctx.send(text)

    @command()
    async def drilify(self, ctx: Context, *, text: clean_content):
        """this Is so coole...."""
        words = text.split(' ')
        after = ''

        for index, word in enumerate(words):
            # randomly capitalize words
            if index % 2 == 0 or random.random() > 0.9:
                words[index] = word.title()

            if (index % 3 == 0 or random.random() > 0.8) and \
                    not word.endswith('e') and \
                    word[-1].lower() not in list('aeiou.,!:'):
                words[index] = word + 'e'

        if random.random() > 0.7:
            after = '.' * random.randint(1, 6)
        else:
            after = ',' if random.random() < 0.8 else ',' * random.randint(1, 2)

        await ctx.send(' '.join(words) + after)

    @command()
    async def ship(self, ctx: Context, a: User, b: User):
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
