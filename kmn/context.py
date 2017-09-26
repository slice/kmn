import discord
from discord import Color, Embed
from discord.ext.commands import Context as DiscordContext


class Context(DiscordContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def confirm(self, **kwargs):
        embed = Embed(**kwargs, color=Color.red())

        # send embed
        try:
            message = await self.send(embed=embed)
        except discord.HTTPException:
            return False

        reactions = {
            '\N{WHITE HEAVY CHECK MARK}': True,
            '\N{CROSS MARK}': False
        }

        # add reactions
        for reaction in reactions.keys():
            try:
                await message.add_reaction(reaction)
            except discord.HTTPException:
                return False

        # only accept reactions from the same person and channel
        def _check(reaction, user):
            return user == self.author and reaction.message.channel == self.channel

        # wait for reaction
        while True:
            reaction, adder = await self.bot.wait_for('reaction_add', check=_check)

            # ignore custom emoji
            if not isinstance(reaction.emoji, str):
                continue

            truth_value = reactions.get(reaction.emoji, None)

            if truth_value is not None:
                await message.delete()
                return truth_value
