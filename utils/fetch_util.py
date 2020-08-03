import discord
from discord.ext import commands


# fetch_guild takes bot discord.Client and guild_id int
#  attempts to fetch guild
#  true on success, false on failure
async def fetch_guild(bot: discord.Client, guild_id: int) -> bool:
    try:
        await bot.fetch_guild(guild_id)
        return True
    except (discord.ext.commands.CommandInvokeError, ValueError, discord.errors.NotFound, discord.errors.Forbidden):
        return False


# fetch_category takes bot discord.Client, channel_id int and guild_id int
#  attempts to fetch category
#  true on success, false on failure
async def fetch_category(bot: discord.Client, channel_id: int, guild_id: int) -> bool:
    ch = await bot.fetch_channel(channel_id)
    if (ch is not None) and (ch.guild.id == guild_id):
        return True
    return False


# fetch_role takes bot discord.Client, channel_id int and guild_id int
#  attempts to fetch category
#  true on success, false on failure
async def fetch_role(bot: discord.Client, role: int, guild_id: int) -> bool:
    try:
        guild = await bot.fetch_guild(guild_id)
        discord.utils.get(guild.roles, id=role)
        return True
    except (discord.ext.commands.CommandInvokeError, ValueError, discord.errors.NotFound, discord.errors.Forbidden):
        return False
