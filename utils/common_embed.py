import discord
import datetime


# common_embed takes title string, description string and fields_dict dictionary
#  creates an embed with title as title, description as description and fields from fields_dict
#  returns the embed
def common_embed(title: str, description: str, fields_dict: dict = {}) -> discord.Embed:
    embed = discord.Embed(title=title, color=0xB00B69)

    embed.timestamp = datetime.datetime.utcnow()
    embed.description = description

    for name, value in fields_dict.items():
        embed.add_field(name=name, value=value, inline=False)

    return embed
