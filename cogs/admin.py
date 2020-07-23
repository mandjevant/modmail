from utils.checks import *
import typing


class adminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn

    @commands.command()
    @is_owner()
    async def reloadcogs(self, ctx):
        self.bot.reload_extension('cogs.admin')
        self.bot.reload_extension('cogs.modmail')

        await ctx.send(f"{ctx.author.mention}, all cogs have been reloaded.")

    @reloadcogs.error
    async def reloadcogs_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def loadcog(self, ctx, cog):
        self.bot.load_extension(cog)
        await ctx.send(f"{ctx.author.mention}, `{cog}` has been loaded.")

    @loadcog.error
    async def loadcog_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def unloadcog(self, ctx, cog):
        self.bot.unload_extension(cog)
        await ctx.send(f"{ctx.author.mention}, `{cog}` has been unloaded.")

    @unloadcog.error
    async def unloadcog_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def query(self, ctx, fetch: str, *, arg: str):

        if fetch == "all":
            i = await self.db_conn.fetch(arg)

            description = ""
            for ret in i:
                description += str(ret) + "\n"
                if len(description) > 850:
                    await ctx.send(description)
                    description = ""

            await ctx.send(description)

        elif fetch == "one":
            i = await self.db_conn.fetchrow(arg)
            value = str(i[0])

            await ctx.send(str(value))

        elif fetch == "commit":
            await self.db_conn.execute(arg)

            await ctx.send(f"`{arg}` Committed the query.")

    @query.error
    async def query_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        elif isinstance(err, commands.BadArgument):
            await ctx.send("Stop being an idiot. Use `.columns` cuz you are a fool.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def columns(self, ctx, table):
        result = dict(await self.db_conn.fetchrow(f'SELECT * FROM {table} LIMIT 1'))
        colnames = str([key for key, value in result.items()])
        await ctx.send(str(colnames))

    @columns.error
    async def columns_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        elif isinstance(err, commands.BadArgument):
            await ctx.send("Please specify an existing table.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    """
    @commands.command()
    @is_owner()
    async def rollback(self, ctx):
        self.db_conn.rollback()
        await ctx.send("Rolled back.")

    @rollback.error
    async def rollback_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")
    """

    @commands.command()
    @is_owner()
    async def purge(self, ctx, n: typing.Optional[int] = 100):
        deleted = await ctx.channel.purge(limit=n)
        await ctx.send(f"Deleted {len(deleted)} message(s).")

    @purge.error
    async def purge_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        elif isinstance(err, commands.BadArgument):
            await ctx.send("Please input an integer.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def allow(self, ctx, *, arg: str):
        for user_id in arg.split(" "):
            if user_id[:2] == "<#":
                pass
            else:
                user_id = user_id[:-1]
                if user_id[:3] == "<@!" or user_id[:2] == "<@":
                    if user_id[:3] == "<@!":
                        user_id = user_id[3:]
                    elif user_id[:2] == "<@":
                        user_id = user_id[2:]

                    await ctx.channel.set_permissions(self.bot.get_user(int(user_id)), read_messages=True,
                                                      send_messages=True, read_message_history=True)
                    await ctx.send("Added " + self.bot.get_user(int(user_id)).mention + " to " + ctx.channel.mention)

    @allow.error
    async def allow_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        elif isinstance(err, commands.BadArgument):
            await ctx.send("Please ping the name of a real user in this guild.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def deny(self, ctx, *, arg: str):
        for user_id in arg.split(" "):
            user_id = user_id[:-1]
            if user_id[:3] == "<@!":
                user_id = user_id[3:]
            else:
                user_id = user_id[2:]

            await ctx.channel.set_permissions(self.bot.get_user(int(user_id)), read_messages=False, send_messages=False,
                                              read_message_history=False)
            await ctx.send("Removed " + self.bot.get_user(int(user_id)).mention + " from " + ctx.channel.mention)

    @deny.error
    async def deny_error(self, ctx, err):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you do not have permission to use this command.")
        elif isinstance(err, commands.BadArgument):
            await ctx.send("Please ping the name of a real user in this channel.")
        else:
            await ctx.send(f"Unknown error occured.\n{str(err)}")


def setup(bot):
    bot.add_cog(adminCog(bot))
