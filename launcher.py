import logging
import json

from kmn.bot import Bot

# setup logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
kmn_logger = logging.getLogger('kmn')
kmn_logger.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter('[{asctime}] [{levelname: <7}] {name}: {message}', '%Y-%m-%d %H:%M:%S', style='{'))
root_logger.addHandler(stream)

# read config
with open('config.json', 'r') as fp:
    config = json.load(fp)

bot = Bot(config=config)
bot.run(config['token'])
