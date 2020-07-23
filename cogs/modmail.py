from checks import *
import typing


class ModmailCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn

    # Reply takes a text of max 2048 characters
    #  replies to modmail with the inputted text
    #  sends reply on success, error on failure
    @commands.command()
    @is_owner()
    async def reply(self, ctx, *, arg):
        await ctx.send(f"Replying to modmail with reply {arg}.")

    # Close takes no arguments
    #  closes the modmail thread aka channel
    #  sends error on failure
    @commands.command()
    @is_owner()
    async def close(self, ctx):
        await ctx.send("Closed modmail")

    # Logs takes no arguments
    #  displays the discord user's past modmails (Perhaps in paginator(s)?)
    #  sends paginator(s) on success, error on failure
    @commands.command()
    @is_owner()
    async def logs(self, ctx):
        await ctx.send("Displaying logs")

    # Mute takes optional user id.
    #  if no user id is given, user id of user in current modmail channel
    #  mutes discord user from modmail
    #  sends confirmation on success, error on failure
    @commands.command()
    @is_owner()
    async def mute(self, ctx, user_id: typing.Optional[str] = ""):
        await ctx.send(f"Muting user {user_id}")

    # Unmute takes optional user id.
    #  if no user id is given, user id of user in current modmail channel
    #  unmutes discord user from modmail
    #  sends confirmation on success, error on failure
    @commands.command()
    @is_owner()
    async def unmute(self, ctx, user_id: typing.Optional[str] = ""):
        await ctx.send(f"Unmuting user {user_id}")

    # Standardreply takes reply_id integer
    #  replies with standard reply
    #  sends reply on success, error on failure
    @commands.command()
    @is_owner()
    async def standardreply(self, ctx, reply_id: int):
        await ctx.send(f"Replying with standard reply {reply_id}")


def setup(bot):
    bot.add_cog(ModmailCog(bot))
