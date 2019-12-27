#!/usr/bin/env python3
# TODO: handle HTTP response errors

import asyncio
from datetime import datetime, timedelta
from functools import wraps
import logging
import os
import re
import time
from urllib.error import URLError
from urllib.request import urlopen

# see https://discordpy.readthedocs.io/en/latest/intro.html
# installing: python3 -m pip install -U discord.py
import discord

OK = 0; VALIDATOR_DOWN = 1; CHAIN_DOWN = 2

validator_name = os.environ.get('CELO_VALIDATOR_NAME', '...default validator name...')
validator_address = os.environ.get('CELO_VALIDATOR_SIGNER_ADDRESS', '...default validator address...')
validator_threshold = timedelta(minutes = 30)
chain_threshold = timedelta(minutes = 5)
check_period_sec = 60
initial_status = OK
# see https://discordpy.readthedocs.io/en/latest/discord.html
discord_bot_token = os.environ.get('CELO_MONITOR_DISCORD_BOT_TOKEN', '...default discord bot token...')
discord_channel_name = os.environ.get('CELO_MONITOR_DISCORD_CHANNEL', '...default discord channel name...')

url = 'https://baklava-blockscout.celo-testnet.org/address/%s/validations?type=JSON' % validator_address
blocks_url = 'https://baklava-blockscout.celo-testnet.org/blocks?type=JSON'
pattern = re.compile(b'data-from-now=\\\\"(.*?)\\\\"')

logging.basicConfig(level = logging.WARNING,
                    format = '%(asctime)s %(name)-14s %(levelname)-8s %(message)s',
                    filename = 'celo_discord_bot.log',
                    filemode = 'a')

client = discord.Client()
celo_channel = [None] # access by reference

# from https://stackoverflow.com/questions/538666/format-timedelta-to-string
def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
        ('year',        60*60*24*365),
        ('month',       60*60*24*30),
        ('day',         60*60*24),
        ('hour',        60*60),
        ('minute',      60),
        ('second',      1)
    ]

    strings=[]
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)

def fromisoformat(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')

# from https://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
def retry(ExceptionToCheck, tries=4, delay=3.0, backoff=2.0):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    logging.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return None
        return f_retry # true decorator
    return deco_retry

@retry(URLError)
def get_last_validated_time():
    f = urlopen(url)
    response = f.read()
    f.close()
    
    match = pattern.search(response)
    # 2019-12-08 11:09:47.000000Z
    if match:
        return fromisoformat(match.group(1).decode('ascii')[:-1])
    else:
        return datetime.min

@retry(URLError)
def get_last_block_time():
    f = urlopen(blocks_url)
    response = f.read()
    f.close()
    
    match = pattern.search(response)
    if match:
        return fromisoformat(match.group(1).decode('ascii')[:-1])
    else:
        return datetime.min

# from https://github.com/Rapptz/discord.py/blob/async/examples/background_task.py
async def background_task():
    await client.wait_until_ready()
    
    status = initial_status
    
    #while not client.is_closed:
    while True:
        if celo_channel[0] is not None:
            last_validated_time = get_last_validated_time()
            last_block_time = get_last_block_time()
            if last_validated_time is None or last_block_time is None:
                logging.warning('cannot probe Celo network status')
                await celo_channel[0].send('[??] cannot probe Celo network status. maybe baklava-blockscout.celo-testnet.org is down.')
                await asyncio.sleep(check_period_sec)
                continue
            
            logging.debug('loop - last validated time %s', last_validated_time)
            now = datetime.utcnow()
            if status == CHAIN_DOWN:
                if now - last_validated_time <= min(chain_threshold, validator_threshold):
                    logging.debug('ok')
                    await celo_channel[0].send('[OK] Celo network got to work.')
                    status = OK
                elif now - last_block_time <= chain_threshold:
                    logging.debug('alert')
                    await celo_channel[0].send('[Alerting] Celo network got to work but %s Celo validator has not produced any blocks yet.' % validator_name)
                    status = VALIDATOR_DOWN
            elif status == VALIDATOR_DOWN:
                if now - last_block_time > chain_threshold:
                    logging.debug('chain down')
                    await celo_channel[0].send('[Chain stopped] Celo network has been stopped, too.')
                    status = CHAIN_DOWN
                elif now - last_validated_time <= validator_threshold:
                    logging.debug('ok')
                    await celo_channel[0].send('[OK] %s Celo validator has restored to producing blocks.' % validator_name)
                    status = OK
            elif status == OK:
                if now - last_block_time > chain_threshold:
                    logging.debug('chain down')
                    await celo_channel[0].send('[Chain stopped] Celo network has been stopped last %s.' % td_format(chain_threshold))
                    status = CHAIN_DOWN
                elif now - last_validated_time > validator_threshold:
                    logging.debug('alert')
                    await celo_channel[0].send('[Alerting] %s Celo validator has not produced any blocks last %s.' % (validator_name, td_format(validator_threshold)))
                    status = VALIDATOR_DOWN
        await asyncio.sleep(check_period_sec)
    logging.warning('background_task() exit')

@client.event
async def on_ready():
    logging.info('We have logged in as {0.user}'.format(client))
    for channel in client.get_all_channels():
        if channel.name == discord_channel_name:
            celo_channel[0] = channel

client.loop.create_task(background_task())
client.run(discord_bot_token)

