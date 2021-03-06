from functools import wraps

import discord
from discord import Color, Member, HTTPException, Role, Permissions
from discord.ext.commands import command, has_permissions, group, bot_has_permissions, guild_only

from kmn.cog import Cog
from kmn.converters import QuickPermissions


def prevent_escalate(func):
    @wraps(func)
    async def new_func(self, ctx, who, *roles):
        for role in roles:
            if ctx.author.top_role < role:
                return await ctx.send(f'{role.name} is higher than your top role.')
        return await func(self, ctx, who, *roles)
    return new_func


class Mod(Cog):
    @group()
    @guild_only()
    @has_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    async def role(self, ctx):
        """manages roles"""

    @role.command(name='vanity')
    @has_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    async def role_vanity(self, ctx, *, name):
        """makes a vanity role"""
        await ctx.guild.create_role(name=name, permissions=Permissions.none(), reason=f'created by {ctx.author}')
        await ctx.ok()

    @role.command(name='give')
    @prevent_escalate
    async def role_give(self, ctx, who: Member, *roles: Role):
        """gives someone a role"""
        await who.add_roles(*roles)
        await ctx.ok()

    @role.command(name='everyone')
    async def role_everyone(self, ctx):
        """toggles mentionable of pseudo here and everyone roles"""
        roles = {
            discord.utils.get(ctx.guild.roles, name='here'),
            discord.utils.get(ctx.guild.roles, name='everyone')
        }

        if None in roles:
            return await ctx.send('`here` and or `everyone` roles were not found.')

        for role in roles:
            try:
                await role.edit(mentionable=not role.mentionable, reason=f'{ctx.prefix}role mention by {ctx.author}')
            except HTTPException:
                return await ctx.send(f'failed to edit {role.name}, probably higher than me.')

        await ctx.ok()

    @role.command(name='take')
    @prevent_escalate
    async def role_take(self, ctx, who: Member, *roles: Role):
        """takes a role from someone"""
        await who.remove_roles(*roles)
        await ctx.ok()

    @command()
    @guild_only()
    @has_permissions(manage_roles=True)
    async def quickrole(self, ctx, role_name, permissions: QuickPermissions(humanize=True)=None, color: Color=None,
                        assign_to: Member=None):
        """quickly creates a role"""
        role = await ctx.guild.create_role(
            reason=f'quickrole by {ctx.author} ({ctx.author.id})',
            name=role_name,
            permissions=permissions,
            color=color
        )

        if assign_to:
            try:
                await assign_to.add_roles(role)
            except HTTPException:
                await ctx.send(f'created role, but failed to assign it to {assign_to}.')
            else:
                await ctx.send(f'created role {role_name} (`{role.id}`) and gave it to {assign_to}!')
        else:
            await ctx.send(f'created role {role_name} (`{role.id}`)')


def setup(bot):
    bot.add_cog(Mod(bot))
