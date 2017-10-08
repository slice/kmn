import asyncio
import logging

from discord import HTTPException, Permissions, Member
from discord.ext.commands import command
from discord.http import Route

from kmn.bot import Bot
from kmn.checks import is_bot_admin
from kmn.cog import Cog

PARTY_PERMISSIONS = {
    'add_reactions', 'read_messages', 'send_messages', 'embed_links', 'attach_files',
    'external_emojis', 'connect', 'speak', 'use_voice_activation', 'change_nickname',
    'read_message_history'
}

log = logging.getLogger(__name__)


class Party(Cog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parties = []

    async def on_member_join(self, member: Member):
        # not a party guild
        if member.guild not in self.parties:
            return

        log.info('%d: announcing party join for %s (%d)', member.guild.id, member, member.id)

        # grab the first text channel and announce the join ;)
        text_channel = member.guild.text_channels[0]
        await text_channel.send(f"\U0001f389 @everyone {member.mention} has joined the party! say hi! \U0001f389")

    @command()
    @is_bot_admin()
    async def party(self, ctx, duration: int=None, *, name=None):
        """launches a party"""

        if duration is not None and duration < 20:
            return await ctx.send('party duration is too low...20 seconds minimum.')

        # start typing
        await ctx.channel.trigger_typing()

        # grab avatar bytes
        async with self.session.get(ctx.author.avatar_url_as(format='png')) as avatar:
            avatar_bytes = await avatar.read()

        # create a guild
        try:
            guild = await ctx.bot.create_guild(
                name=name or f"{ctx.author.name}'s party",
                icon=avatar_bytes
            )

            # wait a little
            await asyncio.sleep(3)
        except HTTPException:
            log.exception('party: failed to create party')
            return await ctx.send("failed to create a party :(")

        # grab from cache
        guild = ctx.bot.get_guild(guild.id)

        # add to party list <3
        self.parties.append(guild)

        # set the default message notifications to mentions only
        await ctx.bot.http.request(
            Route('PATCH', '/guilds/{guild_id}', guild_id=guild.id),
            json={'default_message_notifications': 1}
        )

        # sane permissions
        sane_perms = Permissions()
        for perm in PARTY_PERMISSIONS:
            setattr(sane_perms, perm, True)

        # edit the default role to be sane
        await guild.default_role.edit(permissions=sane_perms, reason="let's get the party started")

        # let's get it started
        text_channel = guild.text_channels[0]
        log.info('%d: sending party started', guild.id)
        await text_channel.send(f"\U0001f44b welcome to **{ctx.author}'s party!** \U0001f44b")

        invite = await text_channel.create_invite()
        external_announcement = await ctx.send(f"\U0001f389 let's get the party started! \U0001f389\n\n{invite}")

        log.info('%d: party has started, woo!', guild.id)

        async def destruction_task():
            log.info('%d: party destruction task: started', guild.id)
            await asyncio.sleep(duration or 60 * 5)  # wait the duration (5 minutes default)
            log.info('%d: party destruction task: 10 seconds left', guild.id)
            await text_channel.send("@everyone \U0001f480 party will end in 10 seconds \U0001f480")
            await asyncio.sleep(10)

            # party is over folks.
            log.info('%d: party is over :(', guild.id)
            self.parties.remove(guild)
            await external_announcement.edit(content=f"{ctx.author}'s party has ended! maybe next time...")
            await guild.delete()

        # party has to end somehow.
        ctx.bot.loop.create_task(destruction_task())


def setup(bot: Bot):
    bot.add_cog(Party(bot))
