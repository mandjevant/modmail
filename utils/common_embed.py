import discord
import datetime


# common_embed takes title string, description string and fields_dict dictionary
#  creates an embed with title as title, description as description and fields from fields_dict
#  returns the embed
def common_embed(title: str, description: str, fields_dict: dict = {}, color: int = 0xB00B69) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)

    embed.timestamp = datetime.datetime.utcnow()
    embed.description = description

    for name, value in fields_dict.items():
        embed.add_field(name=name, value=value, inline=False)

    return embed
