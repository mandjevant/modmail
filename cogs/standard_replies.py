from asyncpg.exceptions import ForeignKeyViolationError

from utils.checks import *
from utils.confirmation import *
from utils.common_embed import *


class standardRepliesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn

    # Standard_reply takes standard_reply_id int.
    #   Retrieves standard reply info from database.
    #   Returns results on success, error on failure.
    @commands.command(aliases=['standardreply'])
    @is_owner()
    async def standard_reply(self, ctx, standard_reply_id: int) -> None:
        result = await self.db_conn.fetchrow("SELECT standardreplies.standard_reply, standardreplies.active, \
                                             standardreplies.description, standardreplies.made_by_id, standardreplies.id, \
                                             categories.category_name, categories.category_id \
                                             FROM modmail.standardreplies \
                                             INNER JOIN modmail.categories \
                                             ON standardreplies.category_id = categories.category_id \
                                             WHERE id = $1", standard_reply_id)

        try:
            made_by = await self.bot.fetch_user(result[3])
            embed = common_embed('Standard Reply',
                                 f"ID: {result[4]}\n\n"
                                 f"Category: {result[5]} (ID: {result[6]})\n"
                                 f"Active: {'✓' if result[1] else '✗'}\n"
                                 f"Made By: {made_by}\n"
                                 f"Reply: \"{result[0]}\"\n"
                                 f"Description: \"{result[2]}\"\n")
        finally:
            await ctx.send(embed=embed)

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

    # Create_standard_reply takes category_id int
    #   Asks for reply and description.
    #   Inserts the reply, description and category_id in the database.
    #   returns confirmation on success, error on failure.
    @commands.command()
    @is_owner()
    async def create_standard_reply(self, ctx, category_id: int) -> None:
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
                                               (standard_reply, made_by_id, active, description, category_id) \
                                               VALUES ($1, $2, true, $3, $4)",
                                           reply.content, ctx.author.id, description.content, category_id)

        except asyncio.TimeoutError:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"You didn't reply within the time limit, please restart with `{ctx.prefix}create_standard_reply`"))
        except ForeignKeyViolationError:
            await ctx.send(embed=common_embed("Standard Reply",
                                              "The id you entered is not a valid category id. Please check the id and try again"))
        else:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully inserted the new standard reply for category id: {category_id}"))

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
    @is_owner()
    async def standard_reply_set_inactive(self, ctx, standard_reply_id: int) -> None:
        msg = await ctx.send(embed=common_embed("Standard Reply", "Setting inactive..."))

        check = await self.db_conn.fetchrow("SELECT active \
                                            FROM modmail.standardreplies \
                                            WHERE id = $1", standard_reply_id)
        if check is None:
            await msg.edit(embed=common_embed("Standard Reply",
                                              "Unable to fetch standard reply, please check if your id is correct"))
            return
        elif not check[0]:
            await msg.edit(embed=common_embed("Standard Reply", "The standard reply is already inactive"))
            return

        try:
            await self.db_conn.execute("UPDATE modmail.standardreplies \
                                        SET active=false \
                                        WHERE id = $1", standard_reply_id)

        finally:
            await msg.edit(embed=common_embed("Standard Reply",
                                              f"Successfully set standard reply inactive with ID: {standard_reply_id}."))

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
    @is_owner()
    async def standard_reply_set_active(self, ctx, standard_reply_id: int) -> None:
        msg = await ctx.send(embed=common_embed("Standard Reply", "Setting active..."))
        check = await self.db_conn.fetchrow("SELECT active \
                                            FROM modmail.standardreplies \
                                            WHERE id = $1", standard_reply_id)
        if check is None:
            await msg.edit(embed=common_embed("Standard Reply",
                                              "Unable to fetch standard reply, please check if your id is correct"))
            return
        elif check[0]:
            await msg.edit(embed=common_embed("Standard Reply", "The standard reply is already active"))
            return

        try:
            await self.db_conn.execute("UPDATE modmail.standardreplies \
                                        SET active=true \
                                        WHERE id = $1", standard_reply_id)

        finally:
            await msg.edit(embed=common_embed("Standard Reply",
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
    @is_owner()
    async def standard_replies(self, ctx) -> None:
        result = await self.db_conn.fetch("SELECT standardreplies.standard_reply, standardreplies.active, \
                                          standardreplies.description, standardreplies.made_by_id, standardreplies.id, \
                                          categories.category_name, categories.category_id \
                                          FROM modmail.standardreplies \
                                          INNER JOIN modmail.categories \
                                          ON standardreplies.category_id = categories.category_id \
                                          WHERE standardreplies.active=true")
        paginator = commands.Paginator()
        try:
            for row in result:
                made_by = await self.bot.fetch_user(row[3])
                paginator.add_line(line=
                                   f"ID: {row[4]}\n\n"
                                   f"Category: {row[5]} (ID: {row[6]})\n"
                                   f"Made By: {made_by}\n"
                                   f"Reply: \"{row[0]}\"\n"
                                   f"Description: \"{row[2]}\"\n"
                                   f"--------------------------------\n")
        finally:
            for page in paginator.pages:
                await ctx.send(embed=common_embed(title="Standard Replies", description=page))

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
    @is_owner()
    async def standard_replies_all(self, ctx) -> None:
        result = await self.db_conn.fetch("SELECT standardreplies.standard_reply, standardreplies.active, \
                                          standardreplies.description, standardreplies.made_by_id, standardreplies.id, \
                                          categories.category_name, categories.category_id \
                                          FROM modmail.standardreplies \
                                          INNER JOIN modmail.categories \
                                          ON standardreplies.category_id = categories.category_id")
        paginator = commands.Paginator()
        try:
            for row in result:
                made_by = await self.bot.fetch_user(row[3])
                paginator.add_line(line=
                                   f"ID: {row[4]}\n\n"
                                   f"Category: {row[5]} (ID: {row[6]})\n"
                                   f"Active: {'✓' if row[1] else '✗'}\n"
                                   f"Made By: {made_by}\n"
                                   f"Reply: \"{row[0]}\"\n"
                                   f"Description: \"{row[2]}\"\n"
                                   f"--------------------------------\n")
        finally:
            for page in paginator.pages:
                await ctx.send(embed=common_embed(title="Standard Replies", description=page))

    @standard_replies_all.error
    async def standard_replies_all_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    @commands.command()
    @is_owner()
    async def edit_standard_reply(self, ctx, standard_reply_id: int):
        try:
            check = await self.db_conn.fetchrow("SELECT id FROM modmail.standardreplies WHERE id=$1", standard_reply_id)
            if not check:
                await ctx.send(embed=common_embed("Standard Reply",
                                                  f"The standard reply with that id doesn't exist,"
                                                  f" please check if it is correct or create it with `{ctx.prefix}create_standard_reply`"))
                return

            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired reply..."))
            reply = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            await ctx.send(embed=common_embed("Standard Reply", "Please enter the desired description..."))
            description = await self.bot.wait_for('message', check=lambda msg: msg.author == ctx.author, timeout=60.0)

            conf = await confirmation(self.bot, ctx, "Standard Reply",
                                      f"**Is this correct?**\n\n"
                                      f"Reply: \"{reply.content}\"\n\n"
                                      f"Description \"{description.content}\"",
                                      "create_standard_reply")
            if conf and check:
                await self.db_conn.execute("UPDATE modmail.standardreplies \
                                            SET standard_reply=$1, description=$2 \
                                            WHERE id=$3", reply.content, description.content, standard_reply_id)

        except asyncio.TimeoutError:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"You didn't reply within the time limit, please restart with `{ctx.prefix}create_standard_reply`"))
        else:
            await ctx.send(embed=common_embed("Standard Reply",
                                              f"Successfully updated the standard reply with id: {standard_reply_id}"))


def setup(bot):
    bot.add_cog(standardRepliesCog(bot))
