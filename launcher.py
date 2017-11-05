import asyncio
import logging
import json
import sys

import aioredis
import asyncpg

from kmn.bot import Bot

# setup logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
kmn_logger = logging.getLogger('kmn')
kmn_logger.setLevel(logging.DEBUG)
stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(logging.Formatter('[{asctime}] [{levelname: <7}] {name}: {message}', '%Y-%m-%d %H:%M:%S', style='{'))
root_logger.addHandler(stream)

# read config
with open('config.json', 'r') as fp:
    config = json.load(fp)


async def launch():
    pool = await asyncpg.create_pool(**config['postgres'])
    redis = await aioredis.create_pool(
        (config['redis']['host'], config['redis']['port']),
        db=config['redis'].get('db', 0)
    )

    bot = Bot(config=config, postgres=pool, redis=redis)
    await bot.start(config['token'])


loop = asyncio.get_event_loop()
loop.run_until_complete(launch())
