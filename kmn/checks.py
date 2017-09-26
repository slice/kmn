from discord.ext import commands


def is_bot_admin():
    def _check(ctx):
        return ctx.author.id in ctx.bot.config.get('admins', [])
    return commands.check(_check)
