import datetime
import pytz
from discord.ext import tasks, commands


class Muted_tasks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn
        self.check_muted.start()

    # Checks for users to unmute
    #  Runs every 30 minutes
    #  Sends nothing on success, raises error on failure
    @tasks.loop(minutes=30.0)
    async def check_muted(self) -> None:
        muted = await self.db_conn.fetch("SELECT user_id, muted_until \
                                          FROM modmail.muted \
                                          WHERE \
                                            active = true")
        for row in muted:
            now = datetime.datetime.now(pytz.utc)
            if row[1] < now:
                await self.db_conn.execute("UPDATE modmail.muted \
                                            SET active = false \
                                            WHERE \
                                                user_id = $1",
                                           int(row[0]))

    # Waits for the bot to be ready before starting the loop
    @check_muted.before_loop
    async def before_check_muted(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Muted_tasks(bot))
