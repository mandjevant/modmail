import time

from utils.checks import *
from utils.common_embed import *
import typing


class adminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn

    # reloadcogs takes no arguments
    #  reloads all cogs
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def reloadcogs(self, ctx) -> None:
        self.bot.reload_extension('cogs.admin')
        self.bot.reload_extension('cogs.modmail')
        self.bot.reload_extension('cogs.muted')
        self.bot.reload_extension('cogs.categories')
        self.bot.reload_extension('cogs.permissions')
        self.bot.reload_extension('cogs.notes')
        self.bot.reload_extension('cogs.standard_replies')
        self.bot.reload_extension('cogs.help')
        self.bot.reload_extension('tasks.muted_tasks')
        self.bot.reload_extension('tasks.message_handling')
        self.bot.reload_extension('tasks.verify_categories_tasks')
        self.bot.reload_extension('tasks.member_join_leave')
        self.bot.reload_extension('tasks.error_handling')

        await ctx.send(embed=common_embed("Reload cogs", f"{ctx.author.mention}, all cogs have been reloaded."))

    # loadcog takes cog str
    #  reloads the cog
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def loadcog(self, ctx, cog: str) -> None:
        self.bot.load_extension(cog)
        await ctx.send(embed=("Load cog", f"{ctx.author.mention}, `{cog}` has been loaded."))

    # unloadcog takes cog str
    #  unloads the cog
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def unloadcog(self, ctx, cog) -> None:
        self.bot.unload_extension(cog)
        await ctx.send(embed=common_embed("Unload cog", f"{ctx.author.mention}, `{cog}` has been unloaded."))

    # query takes fetch str and arg str
    #  runs arg which is query
    #  fetches result based on fetch
    #  sends result
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def query(self, ctx, fetch: str, *, arg: str) -> None:

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

            await ctx.send(embed=common_embed("Query", f"`{arg}` Committed the query."))

    # columns takes table str
    #  gets columns from table
    #  sends columns
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def columns(self, ctx, table) -> None:
        result = dict(await self.db_conn.fetchrow(f'SELECT * FROM {table} LIMIT 1'))
        colnames = str([key for key, value in result.items()])
        await ctx.send(embed=common_embed("Columns", str(colnames)))

    # purge takes optional parameter n int
    #  deletes past n messages
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def purge(self, ctx, n: typing.Optional[int] = 100) -> None:
        deleted = await ctx.channel.purge(limit=n)
        await ctx.send(embed=common_embed("Purge", f"Deleted {len(deleted)} message(s)."))

    # allow takes arg str (users)
    #  allows users in arg to current channel
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def allow(self, ctx, *, arg: str) -> None:
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
                    allow_msg = "Added " + self.bot.get_user(int(user_id)).mention + " to " + ctx.channel.mention
                    await ctx.send(embed=common_embed("Allow", allow_msg))

    # deny takes arg str (users)
    #  denies users in arg from current channel
    #  sends confirmation
    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def deny(self, ctx, *, arg: str) -> None:
        for user_id in arg.split(" "):
            user_id = user_id[:-1]
            if user_id[:3] == "<@!":
                user_id = user_id[3:]
            else:
                user_id = user_id[2:]

            await ctx.channel.set_permissions(self.bot.get_user(int(user_id)), read_messages=False, send_messages=False,
                                              read_message_history=False)
            deny_msg = "Removed " + self.bot.get_user(int(user_id)).mention + " from " + ctx.channel.mention
            await ctx.send(embed=common_embed("Deny", deny_msg))

    @commands.command()
    @is_owner()
    @commands.guild_only()
    async def ping(self, ctx):
        embed = common_embed("", f"Pong! :ping_pong:\n*Bot latency:* {round(self.bot.latency * 1000, 3)}ms")
        t1 = time.perf_counter()
        msg = await ctx.send(embed=embed)
        t2 = time.perf_counter()
        embed = common_embed("", f"Pong! :ping_pong:\n*Bot latency:* {round(self.bot.latency * 1000, 3)}ms\n"
                                 f"*Actual response time:* {round((t2 - t1) * 1000, 3)}ms")
        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(adminCog(bot))
