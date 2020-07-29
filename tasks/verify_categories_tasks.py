import configparser
import json
import discord
from discord.ext import tasks, commands
from utils.common_embed import *
from datetime import datetime


class verifyCategoriesTasks(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db_conn = bot.db_conn
        self.conf = bot.conf
        self.chnl_id = int(bot.conf.get('global', 'modmail_commands_channel_id'))
        self.verify_categories.start()

    # Checks for invalid categories.
    #  Runs every 30 minutes.
    #  Sends nothing on success, raises error on failure
    @tasks.loop(minutes=30.0)
    async def verify_categories(self) -> None:
        results = await self.db_conn.fetch("SELECT category_id, category_name \
                                           FROM modmail.categories \
                                           WHERE active=true")

        owners = [await self.bot.fetch_user(owner) for owner in json.loads(self.conf.get('global', 'owners'))]
        for row in results:
            category = self.bot.get_channel(row[0])
            if category is None:
                chnl = self.bot.get_channel(self.chnl_id)
                embed = common_embed("Categories not correctly synced!",
                                     f"Category ID: `{row[0]}` is not correctly synced.\n\n"
                                     f"**Category '{row[1]}' does not exist or isn't accessible by the bot.\n\n**"
                                     f"Please fix this issue as soon as possible")

                embed.set_image(url='https://i.imgur.com/b8y71CJ.gif')
                await chnl.send(embed=embed)
                await chnl.send(" ".join([owner.mention for owner in owners]) + " <@&718453895550074930>")

            elif category.name.lower() != row[1].lower():
                chnl = self.bot.get_channel(self.chnl_id)
                embed = common_embed("Categories not correctly synced!",
                                     "Category {row[0]} is not correctly synced.\n\n"
                                     f"**Category is named '{row[1]}' in database but is actually called '{category.name}'\n\n**"
                                     f"Please fix this as soon as possible")
                embed.set_image(url='https://i.imgur.com/b8y71CJ.gif')
                await chnl.send(embed=embed)
                await chnl.send(" ".join([owner.mention for owner in owners]) + " <@&718453895550074930>")

    # Waits before bot is ready to start the loop
    @verify_categories.before_loop
    async def before_verify_categories(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(verifyCategoriesTasks(bot))
