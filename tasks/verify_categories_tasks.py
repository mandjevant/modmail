import json
from discord.ext import tasks, commands
from utils.common_embed import *
import asyncio


class verifyCategoriesTasks(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db_conn = bot.db_conn
        self.conf = bot.conf
        self.chnl_id = int(bot.conf.get('global', 'modmail_commands_channel_id'))
        self.verify_categories.start()

    # set_category_inactive takes row
    #  sets category from row to inactive
    #  returns bool
    async def set_category_inactive(self, row) -> bool:
        try:
            await self.db_conn.execute("UPDATE modmail.categories \
                                        SET active=FALSE \
                                        WHERE \
                                           category_id=$1", row[0])
            return True

        except asyncio.exceptions:
            return False

    # Checks for invalid categories.
    #  Runs every 30 minutes.
    #  Sends nothing on success, raises error on failure
    @tasks.loop(minutes=2.0)
    async def verify_categories(self) -> None:
        results = await self.db_conn.fetch("SELECT category_id, category_name, guild_id \
                                            FROM modmail.categories \
                                            WHERE \
                                                active=true")

        owners = [await self.bot.fetch_user(owner) for owner in json.loads(self.conf.get('global', 'owners'))]
        for row in results:
            guild = await self.bot.fetch_guild(row[2])
            admin_role = guild.get_role(self.conf.get('global', 'admin_role_id'))
            chnl = self.bot.get_channel(self.chnl_id)
            category = self.bot.get_channel(row[0])
            if category is None:
                unsync_msg = f"Category ID: `{row[0]}` is not correctly synced.\n\n **Category '{row[1]}' does " \
                             f"not exist or isn't accessible by the bot.\n\n** "
                set_inactive = await self.set_category_inactive(row=row)
                if set_inactive:
                    unsync_msg += f"I set category with category ID: {row[0]} to inactive. Please fix this issue " \
                                  f"and set the category to active. "

            elif category.name.lower() != row[1].lower():
                unsync_msg = f"Category ID: `{row[0]}` is not correctly synced.\n\n **Category is named '{row[1]}'" \
                             f" in database but is actually called '{category.name}'\n\n** "

                set_inactive = await self.set_category_inactive(row=row)

                if set_inactive:
                    unsync_msg += f"I set category with category ID: {row[0]} to inactive. Please fix this issue " \
                                  f"and set the category to active. "
            else:
                continue

            embed = common_embed("Categories not correctly synced!", unsync_msg)
            embed.set_image(url="https://i.imgur.com/b8y71CJ.gif")
            await chnl.send(embed=embed)
            await chnl.send(" ".join([owner.mention for owner in owners]) + admin_role.mention)

    # Waits before bot is ready to start the loop
    @verify_categories.before_loop
    async def before_verify_categories(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(verifyCategoriesTasks(bot))
