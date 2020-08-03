import discord


# get_title_and_description takes bot and row
#  returns title and description of embed
async def get_title_and_description(bot: discord.Client, row):
    try:
        category = await bot.fetch_channel(row[0])
        title = f"Category: {category} ({row[0]})"
    except [discord.DiscordException, discord.NotFound, discord.Forbidden, discord.InvalidArgument]:
        title = f"Category: could not fetch ({row[0]})"
        desc = f"Guild: Could not find.\nRole: could not fetch ({row[2]})\nActive: {row[3]}"
        return title, desc
    try:
        role = discord.utils.get(category.guild.roles, id=row[2])
        desc = f"Guild: {category.guild} ({category.guild.id}).\nRole: {role.mention} ({row[2]})\nActive: {row[3]}"
    except [discord.DiscordException, discord.NotFound, discord.Forbidden, discord.InvalidArgument]:
        desc = f"Guild: {category.guild} ({category.guild.id}).\nRole: could not fetch ({row[2]})\nActive: {row[3]}"

    return title, desc
