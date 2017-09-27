import time

import arrow
import arrow.parser
import discord
from discord import Status
from discord.ext.commands import group, command, clean_content

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.errors import CommandFailure
from kmn.storage import JSONStorage


class HourStyle:
    """Hour styles."""
    MILITARY = 0 # (24-hour)
    AMERICAN = 1 # (12-hour)


TIMEZONE_QUERY = """use `{prefix}t set <timezone>` to set your timezone. with this set, others can check what
time it is for you with `{prefix}t <user>`.

common timezones:

`REGION                 NAME (TYPE)     UTC OFFSET             ATTRIB`
`eastern united states  US/Eastern    | (-05:00, -04:00 DST) | smart |`
`central united states  US/Central    | (-06:00, -05:00 DST) | smart |`
`western united states  US/Pacific    | (-08:00, -07:00 DST) | smart |`
`london                 Europe/London | (+00:00, +01:00 DST) | smart |`
`western european       WET           | (+00:00, +01:00 DST) |       |`
`central european       MET           | (+01:00, +02:00 DST) |       |`
`gmt-8                  Etc/GMT-8     | (+08:00, +08:00 DST) |       |`

you want to type what's in the `NAME` column. a full list of timezones is here:
<https://goo.gl/yQNfZU> type what's under `TZ*`.

setting a manual utc offset (such as `-07:00`, `+08:00`) will prevent automatic daylight saving time
detection, and will force 24-hour mode.
"""


class Timezone(Cog):
    def __init__(self, bot):
        super().__init__(bot)

        # storages
        self.storage = JSONStorage('_timezones.json', loop=bot.loop)
        self.last_message = JSONStorage('_last_message.json', loop=bot.loop)
        self.hour_storage = JSONStorage('_hour_pref.json', loop=bot.loop)

    async def on_message(self, msg):
        if msg.author.bot:
            return

        # put
        await self.last_message.put(str(msg.author.id), time.time())

    def time_for(self, who):
        timezone = self.storage.get(str(who.id), None)

        if not timezone:
            raise CommandFailure(f'{who} has no timezone set.')

        return timezone, arrow.utcnow().to(timezone)

    def format_arrow(self, time):
        return time.format('MMM ddd YYYY-MM-DD HH:mm:ss (hh:mm:ss a)')

    def recently_spoke(self, who):
        last_spoke = self.last_message.get(str(who.id), 0)
        time_since_last = time.time() - last_spoke

        return time_since_last <= 60

    def check_timezone(self, timezone):
        if any(character in timezone for character in ['`', '@', '#']) or len(timezone) > 20:
            raise CommandFailure('that looks like an invalid timezone.')

        try:
            arrow.utcnow().to(timezone)
        except arrow.parser.ParserError:
            raise CommandFailure('invalid timezone.')

    def format_hour_minute(self, who):
        raw, time = self.time_for(who)
        preference = self.hour_storage.get(str(who.id))

        american = 'hh:mm a'
        military = 'HH:mm'

        if preference == HourStyle.AMERICAN:
            return time.format(american)
        elif preference == HourStyle.MILITARY:
            return time.format(military)
        else:
            # infer
            return time.format(american if 'US' in raw else military)

    @group(aliases=['t'], invoke_without_command=True, brief="shows the time for someone")
    async def time(self, ctx, *, who: discord.User=None):
        """command group about time"""
        who = who or ctx.author
        raw_timezone, time = self.time_for(who)
        await ctx.send(f'`{raw_timezone}`: {self.format_arrow(time)}')

    @command()
    async def sleep(self, ctx, *, who: discord.Member=None):
        """tells someone to sleep maybe"""
        who = who or ctx.author

        subject = 'you' if who == ctx.author else 'they'
        subject_external = 'you' if who == ctx.author else 'them'

        # get the time for the person
        _, time = self.time_for(who)

        # format the time for their timezone
        time_formatted = self.format_hour_minute(who)

        if time.hour in {23, 24, 0, 1, 2, 3, 4, 5}:
            if who.status is not Status.online and not self.recently_spoke(who):
                return await ctx.send(f"{who} isn't online, they're probably sleeping.")
            await ctx.send(f"hey {who.mention}, it's {time_formatted}. you should sleep.")
        else:
            await ctx.send(f"{subject} don't need to sleep (it's {time_formatted} for {subject_external}).")

    @time.command(hidden=True)
    @is_bot_admin()
    async def write(self, ctx, who: discord.User, *, timezone):
        """sets someone's timezone"""
        self.check_timezone(timezone)
        await self.storage.put(str(who.id), timezone)
        await ctx.send(f"\N{OK HAND SIGN} set {who}'s timezone to `{timezone}`.")

    @time.command()
    async def hour(self, ctx, *, style):
        """
        sets your hour style (12 hour or 24 hour)

        if you have no hour style, i'll try to guess depending on your timezone. usually, this is a bad
        guess, so you should set it here.
        """
        twelve = {'12 hour', '12', '12-hour', '12h', 'american'}
        military = {'24 hour', '24', '24-hour', '24h', 'military'}

        if style in twelve:
            await self.hour_storage.put(str(ctx.author.id), HourStyle.AMERICAN)
            await ctx.send('\N{OK HAND SIGN} set your style to 12-hour.')
        elif style in military:
            await self.hour_storage.put(str(ctx.author.id), HourStyle.MILITARY)
            await ctx.send('\N{OK HAND SIGN} set your style to 24-hour.')
        elif style in {'reset', 'inferred'}:
            try:
                await self.hour_storage.delete(str(ctx.author.id))
            except KeyError:
                pass
            await ctx.send('\N{OK HAND SIGN} removed your preference.')
        else:
            await ctx.send('unknown hour style! (send `12h` or `24h`).')

    @time.command()
    async def set(self, ctx, *, timezone: clean_content=None):
        """sets your timezone"""

        if not timezone:
            # send some help
            return await ctx.send(TIMEZONE_QUERY.format(prefix=ctx.prefix))

        # check the timezone
        self.check_timezone(timezone)

        # put into storage
        await self.storage.put(str(ctx.author.id), timezone)

        # ok
        await ctx.send(f'ok, your timezone was set to `{timezone}`.')


def setup(bot):
    bot.add_cog(Timezone(bot))
