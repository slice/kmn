import discord
from discord import Message

from kmn.cog import Cog
from kmn.guild_config import GuildConfig


class MessageLogging(Cog):
    async def on_message(self, msg: Message):
        # sent in a dm
        if not msg.guild:
            return

        # only log messages if we are configured to do so
        config = GuildConfig.for_guild(msg.guild, redis=self.bot.redis)
        if not await config.is_set('message_logging'):
            return

        insertion = """
            INSERT INTO messages
            (id, content, created_at, author_id, author_tag, channel_id, channel_name, guild_id, guild_name)
            VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9);
        """

        async with self.bot.postgres.acquire() as conn:
            await conn.execute(
                insertion,

                # base content
                msg.id, msg.content, msg.created_at,

                # author
                msg.author.id, str(msg.author),

                # channel
                msg.channel.id, msg.channel.name,

                # guild
                msg.guild.id, msg.guild.name
            )


def setup(bot):
    bot.add_cog(MessageLogging(bot))
