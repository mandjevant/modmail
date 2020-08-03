from utils.checks import *
from utils.confirmation import *
from utils.reply import *
import disputils


class standardRepliesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn
        self.yellow = 0xE8D90C
        self.green = 0x7CFC00

    @commands.command()
    @has_access()
    @commands.guild_only()
    async def standard_reply(self, ctx, reply_id: int) -> None:
        reply_db = await self.db_conn.fetchrow("SELECT standard_reply \
                                                FROM modmail.standardreplies \
                                                WHERE \
                                                    reply_id=$1 AND \
                                                    active=TRUE",
                                               reply_id)
        conversation = await self.db_conn.fetchrow("SELECT conversation_id, user_id \
                                                    FROM modmail.conversations \
                                                    WHERE \
                                                        channel_id = $1", ctx.channel.id)

        if not reply_db:
            await ctx.send(embed=common_embed("Standard reply",
                                              f"I could not find a reply with reply ID {reply_id}. Please start over."))
            return

        check = await confirmation(self.bot, ctx, "Standard reply",
                                   f"Are you sure you want to reply with `{reply_db[0]}`?", "standard_reply")
        if not check:
            return

        await reply(self.bot, ctx, self.db_conn, conversation[1], reply_db[0], conversation[0])

    @standard_reply.error
    async def standard_reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help standard_reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help standard_reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")
            raise err

    # Standard_reply takes standard_reply_id int.
    #   Retrieves standard reply info from database.
    #   Returns results on success, error on failure.
    @commands.command(aliases=['standardreply'])
    @has_access()
    @commands.guild_only()
    async def show_standard_reply(self, ctx, standard_reply_id: int) -> None:
        result = await self.db_conn.fetchrow("SELECT standard_reply, active, description, made_by_id, reply_id \
                                              FROM modmail.standardreplies \
                                              WHERE \
                                                reply_id = $1", standard_reply_id)

        try:
            made_by = await self.bot.fetch_user(result[3])
            embed = common_embed("Standard Reply",
                                 f"ID: {result[4]}\n\n"
                                 f"Active: {'✓' if result[1] else '✗'}\n"
                                 f"Made By: {made_by}\n"
                                 f"Reply: \"{result[0]}\"\n"
                                 f"Description: \"{result[2]}\"\n")
        finally:
            await ctx.send(embed=embed)

    @show_standard_reply.error
    async def show_standard_reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help show_standard_reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help show_standard_reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # Create_standard_reply takes category_id int
    #   Asks for reply and description.
    #   Inserts the reply, description and category_id in the database.
    #   returns confirmation on success, error on failure.
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def create_standard_reply(self, ctx) -> None:
        try:
            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired reply..."))
            reply = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired description..."))
            description = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            conf = await confirmation(self.bot, ctx, "Standard Reply",
                                      f"**Is this correct?**\n\n"
                                      f"Reply: \"{reply.content}\"\n\n"
                                      f"Description \"{description.content}\"",
                                      "create_standard_reply")
            if conf:
                await self.db_conn.execute("INSERT INTO modmail.standardreplies \
                                            (standard_reply, made_by_id, active, description) \
                                            VALUES ($1, $2, true, $3)",
                                           reply.content, ctx.author.id, description.content)

        except asyncio.TimeoutError:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"You didn't reply within the time limit, please restart with"
                                              f"`{ctx.prefix}create_standard_reply`"))
        else:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully inserted the new standard reply"))

    @create_standard_reply.error
    async def create_standard_reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help create_standard_reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help create_standard_reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # standard_reply_set_inactive takes standard_reply_id int
    #   Sets standard reply inactive.
    #   returns confirmation on success, error on failure.
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def standard_reply_set_inactive(self, ctx, standard_reply_id: int) -> None:
        check = await self.db_conn.fetchrow("SELECT active \
                                             FROM modmail.standardreplies \
                                             WHERE \
                                                reply_id = $1", standard_reply_id)
        if check is None:
            await ctx.send(embed=common_embed("Standard Reply",
                                              "Unable to fetch standard reply, please check if your id is correct"))
            return
        elif not check[0]:
            await ctx.send(embed=common_embed("Standard Reply", "The standard reply is already inactive"))
            return

        check = await confirmation(self.bot, ctx, "Standard reply",
                                   f"Are you sure you want to set standard reply with ID `{standard_reply_id}` "
                                   f"to inactive?", "standard_reply")
        if not check:
            return

        try:
            await self.db_conn.execute("UPDATE modmail.standardreplies \
                                        SET active=false \
                                        WHERE reply_id = $1", standard_reply_id)

        finally:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully set standard reply inactive with "
                                              f"ID: {standard_reply_id}."))

    @standard_reply_set_inactive.error
    async def standard_reply_set_inactive_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(
                f"Bad argument passed. Please type `{self.bot.command_prefix}help standard_reply_set_inactive`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help standard_reply_set_inactive`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # standard_reply_set_active takes standard_reply_id int
    #   Sets standard reply active.
    #   returns confirmation on success, error on failure.
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def standard_reply_set_active(self, ctx, standard_reply_id: int) -> None:
        check = await self.db_conn.fetchrow("SELECT active \
                                             FROM modmail.standardreplies \
                                             WHERE \
                                                reply_id = $1", standard_reply_id)
        if check is None:
            await ctx.send(embed=common_embed("Standard Reply",
                                              "Unable to fetch standard reply, please check if your id is correct"))
            return
        elif check[0]:
            await ctx.send(embed=common_embed("Standard Reply", "The standard reply is already active"))
            return

        check = await confirmation(self.bot, ctx, "Standard reply",
                                   f"Are you sure you want to set standard reply with ID `{standard_reply_id}` "
                                   f"to active?", "standard_reply")
        if not check:
            return

        try:
            await self.db_conn.execute("UPDATE modmail.standardreplies \
                                        SET active=true \
                                        WHERE \
                                            reply_id = $1", standard_reply_id)

        finally:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully set standard reply active with ID: {standard_reply_id}."))

    @standard_reply_set_active.error
    async def standard_reply_set_active_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(
                f"Bad argument passed. Please type `{self.bot.command_prefix}help standard_reply_set_active`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help standard_reply_set_active`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # standard_replies takes no arguments
    #   Retrieves all active standard replies in database
    #   returns results on success, error on failure.
    @commands.group(invoke_without_command=True, aliases=['standardreplies'])
    @has_access()
    @commands.guild_only()
    async def standard_replies(self, ctx) -> None:
        result = await self.db_conn.fetch("SELECT standardreplies.standard_reply, standardreplies.active, \
                                                  standardreplies.description, standardreplies.made_by_id, \
                                                  standardreplies.reply_id \
                                           FROM modmail.standardreplies \
                                           WHERE standardreplies.active=true")
        embeds = list()
        try:

            for row in result:
                made_by = await self.bot.fetch_user(row[3])
                embeds.append(common_embed(f"ID: {row[4]}\n\n",
                                           f"Made By: {made_by}\n"
                                           f"Reply: \"{row[0]}\"\n"
                                           f"Description: \"{row[2]}\"\n"))
        finally:
            await disputils.BotEmbedPaginator(ctx, embeds).run()

    @standard_replies.error
    async def standard_replies_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # standard_replies all takes no arguments
    #   Retrieves all standard replies in database, no matter if active or not.
    #   returns results on success, error on failure.
    @standard_replies.command(name='all')
    @has_access()
    @commands.guild_only()
    async def standard_replies_all(self, ctx) -> None:
        result = await self.db_conn.fetch("SELECT standardreplies.standard_reply, standardreplies.active, \
                                                  standardreplies.description, standardreplies.made_by_id, \
                                                  standardreplies.reply_id \
                                           FROM modmail.standardreplies")
        embeds = list()
        try:

            for row in result:
                made_by = await self.bot.fetch_user(row[3])
                embeds.append(common_embed(f"ID: {row[4]}\n\n",
                                           f"Active: {'✓' if row[1] else '✗'}\n"
                                           f"Made By: {made_by}\n"
                                           f"Reply: \"{row[0]}\"\n"
                                           f"Description: \"{row[2]}\"\n"))
        finally:
            await disputils.BotEmbedPaginator(ctx, embeds).run()

    @standard_replies_all.error
    async def standard_replies_all_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def edit_standard_reply(self, ctx, standard_reply_id: int):
        try:
            check = await self.db_conn.fetchrow("SELECT reply_id \
                                                 FROM modmail.standardreplies \
                                                 WHERE \
                                                    reply_id=$1", standard_reply_id)
            if not check:
                await ctx.send(embed=common_embed("Standard Reply",
                                                  f"The standard reply with that id doesn't exist, "
                                                  f"please check if it is correct or create it with "
                                                  f"`{ctx.prefix}create_standard_reply`"))
                return

            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired reply..."))
            reply = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired description..."))
            description = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            conf = await confirmation(self.bot, ctx, "Standard Reply",
                                      f"**Is this correct?**\n\n"
                                      f"Reply: '{reply.content}'\n\n"
                                      f"Description '{description.content}'",
                                      "create_standard_reply")
            if conf and check:
                await self.db_conn.execute("UPDATE modmail.standardreplies \
                                            SET standard_reply=$1, description=$2 \
                                            WHERE \
                                                reply_id=$3", reply.content, description.content, standard_reply_id)

        except asyncio.TimeoutError:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"You didn't reply within the time limit, please restart with "
                                              f"`{ctx.prefix}create_standard_reply`"))
        else:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully updated the standard reply with id: {standard_reply_id}"))

    @edit_standard_reply.error
    async def edit_standard_reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help edit_standard_reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help edit_standard_reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")


def setup(bot):
    bot.add_cog(standardRepliesCog(bot))
