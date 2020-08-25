from discord.ext import commands
from utils.common_embed import *
import asyncio
import typing


# the class category selector is for the user side
#  The user can select what category their modmail is for
class category_selector:
    # Run takes bot commands.Bot, channel discord.Text, user discord.User, delete_message bool default False
    #   Asks the user for the desired category and listens for reaction
    #   on_reaction => check the database if the reaction is valid and sends error if not
    #   returns discord.CategoryChannel and discord.Guild on success, None on failure
    @staticmethod
    async def start_embed(bot: commands.Bot, channel: discord.TextChannel, user: discord.User,
                          delete_message: bool = False) -> \
            typing.Optional[typing.Tuple[discord.CategoryChannel, discord.Guild]]:

        try:
            categories = await bot.db_conn.fetch("SELECT category_name, emote_id \
                                                  FROM modmail.categories \
                                                  WHERE \
                                                    active=true")
            embed = common_embed("Category Selector",
                                 "Please react with the corresponding emote for your desired category")

            embed.add_field(name="Available categories: ",
                            value="\n".join([f"{row[0].capitalize()} = {row[1]}" for row in categories]))
            msg = await channel.send(embed=embed)

            for row in categories:
                await msg.add_reaction(row[1])

            reaction, _ = await bot.wait_for("reaction_add",
                                             check=lambda react,
                                                          react_user: react.message.id == msg.id and react_user == user,
                                             timeout=120)

            db_category = await bot.db_conn.fetchrow("SELECT category_id, guild_id \
                                                      FROM modmail.categories \
                                                      WHERE \
                                                        emote_id=$1 AND \
                                                        active=true",
                                                     reaction.emoji)

            if not db_category:
                await msg.edit(embed=common_embed("Invalid Reaction",
                                                  "What the heck, you should be using the existing emotes not new "
                                                  "ones. Please restart the process and try again"))
                return

        except asyncio.TimeoutError:
            await channel.send("You didn't answer in time, please restart the process by sending your message "
                               "again")
            return

        else:
            category = bot.get_channel(db_category[0])
            guild = bot.get_guild(db_category[1])
            if delete_message:
                await asyncio.sleep(2)
                await msg.delete()

            return category, guild
