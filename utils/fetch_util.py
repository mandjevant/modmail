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
    guild = discord.utils.get(bot.guilds, id=guild_id)
    category_list = list()
    for guild in guild.by_category():
        category_list.append(guild[0])
    ch = discord.utils.get(category_list, id=channel_id)
    if ch is not None:
        return True
    return False
