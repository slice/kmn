from discord import Permissions
from discord.ext.commands import Converter, BadArgument


class QuickPermissions(Converter):
    def __init__(self, *, humanize=False):
        self.humanize = humanize

    async def convert(self, ctx, argument):
        if self.humanize:
            argument = argument.replace('server', 'guild')

        permissions = Permissions()

        for key in argument.split(','):
            if not hasattr(permissions, key):
                # TODO: clean key
                raise BadArgument(f'invalid permission key: {key}')

            # set permission
            setattr(permissions, key.strip(), True)

        return permissions
