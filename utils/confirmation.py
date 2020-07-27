from utils.common_embed import *
import asyncio


# confirmation takes title str, confirmation_msg_input str and command str (name of command)
#  asks user for confirmation of action through reactions
#  returns bool based on reaction
async def confirmation(bot, ctx, title: str, confirmation_msg_input: str, command: str) -> bool:
    confirmation_msg = await ctx.send(embed=common_embed(title, confirmation_msg_input))
    await confirmation_msg.add_reaction("✅")
    await confirmation_msg.add_reaction("❌")

    try:
        def is_category_emoji(react, user):
            return react.message.id == confirmation_msg.id and user == ctx.message.author

        reaction, _ = await bot.wait_for('reaction_add', check=is_category_emoji, timeout=30)

        await confirmation_msg.add_reaction(reaction.emoji)

        if reaction.emoji not in ["✅", "❌"]:
            await confirmation_msg.edit(embed=common_embed(title,
                                                           "Shaking my fucking head. Please start over and don't "
                                                           "be a fool."))
            return False
        elif reaction.emoji == "❌":
            await confirmation_msg.edit(embed=common_embed(title,
                                                           "The request is cancelled. "
                                                           f"Type `!help {command}` to start over."))
            return False
        elif reaction.emoji == "✅":
            await confirmation_msg.edit(embed=common_embed(title,
                                                           f"The {title.lower()} request is confirmed."))
        return True

    except asyncio.TimeoutError:
        await confirmation_msg.edit(embed=common_embed(title,
                                                       "Looks like you waited too long. Please restart the process."))
        return False
