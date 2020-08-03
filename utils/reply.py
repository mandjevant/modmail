from utils.common_embed import *
from discord.ext import commands
import asyncpg

yellow = 0xE8D90C
green = 0x7CFC00


# Reply takes bot commands.Bot, ctx commands.Context, db_conn asyncpg.Pool, user_id int,
#    message str, conv_id int and anon bool default false
#  if anon true => Replies to user anonymously
#  else replies to user
#  returns nothing on success, error on failure
async def reply(bot: commands.Bot, ctx: commands.Context, db_conn: asyncpg.pool.Pool, user_id: int, message: str,
                conv_id: int, anon: bool = False) -> None:
    user = bot.get_user(user_id)

    usr_embed = common_embed("", message, color=yellow)
    if anon:
        usr_embed.set_author(name="Moderator")
    else:
        usr_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        usr_embed.set_footer(text=ctx.author.roles[-1].name)
    usr_msg = await user.send(embed=usr_embed)

    thread_embed = common_embed("", message, color=green)
    thread_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    thread_embed.set_footer(text=ctx.author.roles[-1].name if not anon else "anonymous reply")
    mod_msg = await ctx.send(embed=thread_embed)

    await db_conn.execute("INSERT INTO modmail.messages \
                           (message_id, message, author_id, conversation_id, other_side_message_id, made_by_mod) \
                           VALUES ($1, $2, $3, $4, $5, true)",
                          mod_msg.id, message, ctx.author.id, conv_id, usr_msg.id)

    await ctx.message.delete()
