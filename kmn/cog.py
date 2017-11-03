from aiohttp import ClientSession


class Cog:
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

        # not particularly proud of this
        mangle_key = f'_{type(self).__name__}__unload'
        self._original_unload = getattr(self, mangle_key, None)
        setattr(self, mangle_key, self.__unload)

    @property
    def pg(self):
        """Shortcut to ``Bot.postgres``."""
        return self.bot.postgres

    @property
    def redis(self):
        """Shortcut to ``Bot.redis``."""
        return self.bot.redis

    def __unload(self):
        self.session.close()
        if self._original_unload:
            self._original_unload()
