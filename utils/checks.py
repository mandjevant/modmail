import configparser
import json
from discord.ext import commands


# exc is an exception handler wrapper.
#  it's neat
def exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return False

    return wrapper


# owner_check takes context
#  checks if user in context is an owner
#  returns boolean
@exc
def owner_check(ctx) -> bool:
    config = configparser.ConfigParser()
    config.read('./conf.ini')
    owners = json.loads(config.get('global', 'owners'))

    return ctx.author.id in owners


def is_owner():
    async def wrapper(ctx):
        return owner_check(ctx)

    return commands.check(wrapper)
