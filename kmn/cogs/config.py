from collections import namedtuple

from discord import Color, Embed, HTTPException
from discord.ext.commands import group, guild_only, clean_content, has_permissions

from kmn.bot import PREFIXES_KEY
from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.context import Context


class Field(namedtuple('Field', 'type description')):
    """A configuration field."""


def pretty_boolean(value):
    if value not in {'off', 'on', 'true', 'false'}:
        raise ValueError('invalid boolean')


SCHEMA_PRETTY = {
    float: 'floating-point number',
    int: 'integer',
    str: 'text',
    pretty_boolean: 'true or false'
}


class Config(Cog):
    SCHEMA = {
        'message_logging': Field(type=pretty_boolean, description='makes me log all messages i can see in this server.')
    }

    @group(aliases=['config'])
    @has_permissions(manage_guild=True)
    @guild_only()
    async def cfg(self, ctx):
        """manages this server's configuration"""

    @cfg.command()
    @guild_only()
    @has_permissions(manage_nicknames=True)
    async def nick(self, ctx, *, nick: clean_content):
        """change the nickname of the bot"""
        try:
            await ctx.guild.me.edit(nick=nick)
            await ctx.ok()
        except HTTPException as err:
            await ctx.fail('edit nick', err)

    @cfg.command()
    @is_bot_admin()
    async def username(self, ctx, *, username: clean_content):
        """change the username of the bot"""
        try:
            await ctx.bot.user.edit(username=username)
            await ctx.ok()
        except HTTPException as err:
            await ctx.fail('edit username', err)

    @cfg.group()
    @guild_only()
    async def prefix(self, ctx):
        """manages prefixes"""

    @prefix.command(name='add')
    async def prefix_add(self, ctx: Context, *, prefix: clean_content):
        """add a prefix"""
        with await self.redis as conn:
            await conn.sadd(PREFIXES_KEY.format(ctx.guild), prefix)
        await ctx.ok()

    @prefix.command(name='remove')
    async def prefix_remove(self, ctx: Context, *, prefix: clean_content):
        """remove a prefix"""
        if len(await ctx.bot.get_prefixes_for(ctx.guild)) == 1:
            return await ctx.send("you can't remove the only prefix, lol.")

        with await self.redis as conn:
            await conn.srem(PREFIXES_KEY.format(ctx.guild), prefix)
        await ctx.ok()

    @prefix.command(name='list')
    async def prefix_list(self, ctx: Context):
        """list prefixes"""
        embed = Embed(color=Color.blurple(), title='prefixes')
        embed.set_footer(text='mentioning me will always work')
        embed.description = '\n'.join(['\N{BULLET} ' + prefix for prefix in await ctx.bot.get_prefixes_for(ctx.guild)])
        await ctx.send(embed=embed)

    @cfg.command(name='schema')
    async def cfg_schema(self, ctx):
        """lists config keys"""
        if not self.SCHEMA:
            return await ctx.send('there are no config fields.')

        lines = [f'{key}: `{SCHEMA_PRETTY[value.type]}`, {value.description}' for key, value in self.SCHEMA.items()]
        await ctx.send('\n'.join(lines))

    @cfg.command(name='set')
    async def cfg_set(self, ctx, key: clean_content, *, value: clean_content):
        """sets a configuration key"""

        if key not in self.SCHEMA:
            return await ctx.send('that key is invalid.')

        schema_field = self.SCHEMA[key]

        # validate that the value of the configuration key is well formed.
        try:
            schema_field.type(value)
        except ValueError:
            return await ctx.send(f"that key is not a valid {SCHEMA_PRETTY[schema_type.type]}.")

        await ctx.config.set(key, value)
        await ctx.send('\N{OK HAND SIGN} set.')


def setup(bot):
    bot.add_cog(Config(bot))
