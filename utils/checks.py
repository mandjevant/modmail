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
async def owner_check(ctx) -> bool:
    config = configparser.ConfigParser()
    config.read('./conf.ini')

    return ctx.author.id in json.loads(config.get('global', 'owners'))


# access_check takes context and db_conn asyncpg.pool.Pool
#  checks if user has roles that have access to category
#  returns boolean
@exc
async def access_check(ctx) -> bool:
    result = await ctx.bot.db_conn.fetch("SELECT permissions.role_id \
                                          FROM modmail.categories \
                                          JOIN modmail.permissions ON permissions.category_id=categories.category_id \
                                          WHERE \
                                             categories.category_id=$1 AND \
                                             permissions.active=TRUE AND \
                                             categories.active=TRUE;", ctx.channel.category.id)
    if result:
        return len(set([row['role_id'] for row in result]) & set([role.id for role in ctx.author.roles])) > 0
    return False


# admin_check takes context
#  checks if user has admin role
#  returns boolean
@exc
async def admin_check(ctx) -> bool:
    config = configparser.ConfigParser()
    config.read('./conf.ini')

    return int(config.get('global', 'admin_role_id')) in [role.id for role in ctx.author.roles]


# bot_commands_ch_check takes context
#  checks if command was typed in bot commands channel
#  returns boolean
@exc
async def bot_commands_ch_check(ctx) -> bool:
    config = configparser.ConfigParser()
    config.read('./conf.ini')

    return int(ctx.channel.id) == int(config.get('global', 'modmail_commands_channel_id'))


def is_owner():
    async def wrapper(ctx):
        return await owner_check(ctx)

    return commands.check(wrapper)


def is_admin():
    async def wrapper(ctx):
        return (await admin_check(ctx) and await bot_commands_ch_check(ctx)) or await owner_check(ctx)

    return commands.check(wrapper)


def has_access():
    async def wrapper(ctx):
        return await access_check(ctx) or await admin_check(ctx) or await owner_check(ctx)

    return commands.check(wrapper)
