GUILD_KEY = 'guild_config:{0.id}:{1}'


class GuildConfig:
    """An object that manages the configuration of this guild through Redis."""

    def __init__(self, guild, *, redis):
        self.guild = guild
        self.redis = redis

    async def set(self, key, value):
        with await self.redis as conn:
            await conn.set(GUILD_KEY.format(self.guild, key), value)

    async def get(self, key, *, cast=None):
        with await self.redis as conn:
            result = (await conn.get(GUILD_KEY.format(self.guild, key))).decode()
            return cast(result) if cast else result
