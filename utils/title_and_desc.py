import discord


# get_title_and_description takes bot and row
#  returns title and description of embed
#####################################################
#  I'm only putting this here since it's super ugly.
#  I'll fix it some time.
async def get_title_and_description(bot: discord.Client, row):
    try:
        category = await bot.fetch_channel(row[0])
    except:
        category = None
    try:
        role = discord.utils.get(category.guild.roles, id=row[2])
    except:
        role = None
    if category is None and role is not None:
        title = f"Category: could not fetch ({row[0]})"
        desc = f"Guild: Could not find.\nRole: {role} ({row[2]})\nActive: {row[3]}"
    elif category is None and role is None:
        title = f"Category: could not fetch ({row[0]})"
        desc = f"Guild: Could not find.\nRole: could not fetch ({row[2]})\nActive: {row[3]}"
    elif category is not None and role is None:
        title = f"Category: {category} ({row[0]})"
        desc = f"Guild: {category.guild} ({category.guild.id}).\nRole: could not fetch ({row[2]})\nActive: {row[3]}"
    elif category is not None and role is not None:
        title = f"Category: {category} ({row[0]})"
        desc = f"Guild: {category.guild} ({category.guild.id}).\nRole: {role.mention} ({row[2]})\nActive: {row[3]}"

    return title, desc
