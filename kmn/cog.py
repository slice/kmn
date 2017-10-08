from aiohttp import ClientSession


class Cog:
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

        # not particularly proud of this
        mangle_key = f'_{type(self).__name__}__unload'
        self._original_unload = getattr(self, mangle_key, None)
        setattr(self, mangle_key, self.__unload)

    def __unload(self):
        self.session.close()
        if self._original_unload:
            self._original_unload()
