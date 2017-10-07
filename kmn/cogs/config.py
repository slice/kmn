from collections import namedtuple

from discord.ext.commands import group, guild_only, clean_content, has_permissions

from kmn.cog import Cog


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
    }

    @group(aliases=['config'])
    @has_permissions(manage_guild=True)
    @guild_only()
    async def cfg(self, ctx):
        """manages this server's configuration"""

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
            return await ctx.send('That key is not valid.')

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
