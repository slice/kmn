import logging
import json

from kmn.bot import Bot

# setup logging
logging.basicConfig(level=logging.INFO)

# read config
with open('config.json', 'r') as fp:
    config = json.load(fp)

bot = Bot(config=config)
bot.run(config['token'])
