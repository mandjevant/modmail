from utils.confirmation import *
from utils.fetch_util import *
from utils.checks import *
import discord
from discord.ext import commands
import disputils
import asyncio


class CategoriesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = self.bot.db_conn

    # link_category takes category_id int and guild_id int
    #  makes sure the category and the guild are real and reachable
    #  asks the user to react with an emoji
    #  checks if category and emoji not in database yet
    @commands.command(pass_context=True)
    @is_admin()
    @commands.guild_only()
    async def link_category(self, ctx, category_id: int, guild_id: int) -> None:
        if not await fetch_guild(self.bot, guild_id):
            await ctx.send(embed=common_embed("Link category",
                                              "Unable to fetch guild. Please check if the ID is correct."))
            return

        if not await fetch_category(self.bot, category_id, guild_id):
            await ctx.send(embed=common_embed("Link category",
                                              "Unable to fetch category. Please check if the ID is correct."))
            return

        msg = await ctx.send(embed=common_embed("Link category", "Please react to this message with an emoji you "
                                                                 "want to use for this category. Please make sure "
                                                                 "this is a standard emoji aka not a custom server "
                                                                 "emoji. You have 30 seconds."))

        try:
            def is_category_emoji(react, user):
                return react.message.id == msg.id and user == ctx.message.author

            reaction, _ = await self.bot.wait_for('reaction_add', check=is_category_emoji, timeout=30)

            await msg.add_reaction(reaction.emoji)
            await msg.edit(embed=common_embed("Link category", "Success! I'm setting the category."))

        except asyncio.TimeoutError:
            await msg.edit(embed=common_embed("Link category",
                                              "Looks like you waited too long. Please restart the process."))
            return

        category_result = await self.db_conn.fetchrow("SELECT active \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_id=$1", int(category_id))
        if category_result:
            if category_result[0]:
                await ctx.send(embed=common_embed('Link category',
                                                  "This category is already active and linked to the id provided"))
            elif not category_result[0]:
                confirm = await confirmation(self.bot, ctx, 'Link category',
                                             'The category is already in the database and linked.\n'
                                             'But not set active, do you wan\'t to set it active?',
                                             'link_category')
                if confirm:  # If the request is accepted update the database
                    await self.db_conn.execute("UPDATE modmail.categories \
                                                SET active=true \
                                                WHERE \
                                                    category_id=$1",
                                               category_id)
            else:
                await ctx.send(embed=common_embed("Link category",
                                                  "This category is already in the database. Please set a different "
                                                  "category."))
            return

        emote_result = await self.db_conn.fetchrow("SELECT * \
                                                    FROM modmail.categories \
                                                    WHERE \
                                                        emote_id=$1", reaction.emoji)

        if emote_result:
            await ctx.send(embed=common_embed("Link category",
                                              "This emoji is already in the database. Please set a different "
                                              "emoji."))
            return

        category = await self.bot.fetch_channel(category_id)

        await self.db_conn.execute("INSERT INTO modmail.categories \
                                    (category_id, category_name, active, guild_id, emote_id) \
                                    VALUES($1, $2, TRUE, $3, $4)",
                                   category_id, category.name, guild_id, reaction.emoji)

        await ctx.send(embed=common_embed("Link category", "Success! The category is successfully registered."))

    @link_category.error
    async def link_category_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help link_category`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help link_category`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # create_category takes guild_id int and category_name name
    #  makes sure the guild is reachable and permissions are set
    #  asks the user to react with an emoji
    #  checks if emoji is not in database yet
    #  creates category and inputs category in database
    @commands.command(pass_context=True)
    @is_admin()
    @commands.guild_only()
    async def create_category(self, ctx, guild_id: int, category_name: str) -> None:
        if not await fetch_guild(self.bot, guild_id):
            await ctx.send(embed=common_embed("Link category",
                                              "Unable to fetch guild. Please check if the ID is correct."))
            return

        category_result = await self.db_conn.fetchrow("SELECT * \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_name=$1", category_name)
        if category_result:
            await ctx.send(embed=common_embed("Create category",
                                              "This category name is already in the database. Please set a different "
                                              "category name."))
            return

        msg = await ctx.send(embed=common_embed("Create category", "Please react to this message with an emoji you "
                                                                   "want to use for this category. Please make sure "
                                                                   "this is a standard emoji aka not a custom server "
                                                                   "emoji. You have 30 seconds."))

        try:
            def is_category_emoji(react, user):
                return react.message.id == msg.id and user == ctx.message.author

            reaction, _ = await self.bot.wait_for('reaction_add', check=is_category_emoji, timeout=30)

            await msg.add_reaction(reaction.emoji)
            await msg.edit(embed=common_embed("Create category", "Success! I'm setting the category."))

        except asyncio.TimeoutError:
            await msg.edit(embed=common_embed("Create category",
                                              "Looks like you waited too long. Please restart the process."))
            return

        emote_result = await self.db_conn.fetchrow("SELECT * \
                                                    FROM modmail.categories \
                                                    WHERE \
                                                        emote_id=$1", reaction.emoji)

        if emote_result:
            await ctx.send(embed=common_embed("Create category",
                                              "This emoji is already in the database. Please set a different "
                                              "emoji."))
            return

        try:
            category = await ctx.guild.create_category(category_name)
            await category.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False,
                                           read_message_history=False)
        except (discord.ext.commands.MissingPermissions, discord.errors.Forbidden):
            await ctx.send(embed=common_embed("Create category",
                                              "Oof, I'm missing permissions. Please add them and try again."))
            return
        except Exception as e:
            await ctx.send(embed=common_embed("Create category",
                                              "Oof, I'm missing permissions. Please add them and try again."))
            return

        await self.db_conn.execute("INSERT INTO modmail.categories \
                                    (category_id, category_name, active, guild_id, emote_id) \
                                    VALUES($1, $2, TRUE, $3, $4)",
                                   category.id, category_name, guild_id, reaction.emoji)

        await ctx.send(embed=common_embed("Create category", "Success! The category is successfully registered."))

    @create_category.error
    async def create_category_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help create_category`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help create_category`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # update_emote takes category_id int
    #  makes sure the category is real
    #  asks confirmation for the request
    #  asks the user to react with an emoji
    #  checks if emoji not in database yet
    #  updates emote in database
    @commands.command(pass_context=True)
    @is_admin()
    @commands.guild_only()
    async def update_emote(self, ctx, category_id: int) -> None:
        category_result = await self.db_conn.fetchrow("SELECT category_name, emote_id \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_id=$1", category_id)

        if not category_result:
            await ctx.send(embed=common_embed("Update emote",
                                              "I do not recognize this category id. Did you make a typo?"))
            return

        success = await confirmation(self.bot, ctx, "Update emote",
                                     f"The current emote for category {category_result[0]} is {category_result[1]} "
                                     f"are you sure you want to change it?",
                                     "update_emote")

        if not success:
            return

        msg = await ctx.send(embed=common_embed("Update emote", "Please react to this message with an emoji you "
                                                                "want to use for this category. Please make sure "
                                                                "this is a standard emoji aka not a custom server "
                                                                "emoji. You have 30 seconds."))

        try:
            def is_category_emoji(react, user):
                return react.message.id == msg.id and user == ctx.message.author

            reaction, _ = await self.bot.wait_for('reaction_add', check=is_category_emoji, timeout=30)

            await msg.add_reaction(reaction.emoji)
            await msg.edit(embed=common_embed("Update emote", "Success! I'm setting the category."))

        except asyncio.TimeoutError:
            await msg.edit(embed=common_embed("Update emote",
                                              "Looks like you waited too long. Please restart the process."))
            return

        emote_result = await self.db_conn.fetchrow("SELECT * \
                                                    FROM modmail.categories \
                                                    WHERE \
                                                        emote_id=$1", reaction.emoji)

        if emote_result:
            await ctx.send(embed=common_embed("Update emote",
                                              "This emoji is already in the database. Please set a different "
                                              "emoji."))
            return

        await self.db_conn.execute("UPDATE modmail.categories \
                                    SET emote_id=$1 \
                                    WHERE \
                                      category_id=$2",
                                   reaction.emoji, category_id)

    @update_emote.error
    async def update_emote_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help update_emote`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help update_emote`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # category_set_active takes category_id int
    #  makes sure the category is real and is inactive
    #  asks confirmation for the request
    #  sets category to active
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def category_set_active(self, ctx, category_id: int) -> None:
        category_result = await self.db_conn.fetchrow("SELECT category_name, active \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_id=$1", category_id)

        if not category_result:
            await ctx.send(embed=common_embed("Category set active",
                                              "I do not recognize this category id. Did you make a typo?"))
            return

        if category_result[1]:
            await ctx.send(embed=common_embed("Category set active",
                                              f"This category with name {category_result[0]} is already active. "
                                              f"Did you mean `{self.bot.command_prefix}category_set_inactive "
                                              f"{category_id}`?"))
            return

        success = await confirmation(self.bot, ctx, "Category set active",
                                     f"Are you sure you want to activate {category_result[0]}?", "category_set_active")

        if not success:
            return

        await self.db_conn.execute("UPDATE modmail.categories \
                                    SET active=TRUE \
                                    WHERE \
                                      category_id=$1", category_id)

    @category_set_active.error
    async def category_set_active_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help category_set_active`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help category_set_active`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # category_set_inactive takes category_id int
    #  makes sure the category is real and is active
    #  asks confirmation for the request
    #  sets category to inactive
    @commands.command(aliases=['delete_category'])
    @is_admin()
    @commands.guild_only()
    async def category_set_inactive(self, ctx, category_id: int) -> None:
        category_result = await self.db_conn.fetchrow("SELECT category_name, active \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_id=$1", category_id)

        if not category_result:
            await ctx.send(embed=common_embed("Category set inactive",
                                              "I do not recognize this category id. Did you make a typo?"))
            return

        if not category_result[1]:
            await ctx.send(embed=common_embed("Category set inactive",
                                              f"This category with name {category_result[0]} is already inactive. "
                                              f"Did you mean `{self.bot.command_prefix}category_set_active "
                                              f"{category_id}`?"))
            return

        success = await confirmation(self.bot, ctx, "Category set inactive",
                                     f"Are you sure you want to deactivate {category_result[0]}?",
                                     "category_set_inactive")

        if not success:
            return

        await self.db_conn.execute("UPDATE modmail.categories \
                                    SET active=FALSE \
                                    WHERE \
                                      category_id=$1", category_id)

    @category_set_inactive.error
    async def category_set_inactive_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help category_set_inactive`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help category_set_inactive`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # categories takes no parameters
    #  gets all active modmail categories
    #  sends result on success, error on failure
    @commands.group(invoke_without_command=True)
    @is_admin()
    @commands.guild_only()
    async def categories(self, ctx) -> None:
        msg = await ctx.send(embed=common_embed("Categories", "Retrieving active categories."))

        results = await self.db_conn.fetch("SELECT category_id, guild_id, emote_id \
                                            FROM modmail.categories \
                                            WHERE \
                                               active=TRUE")
        embeds = list()

        for row in results:
            guild = await self.bot.fetch_guild(row[1])
            category = await self.bot.fetch_channel(row[0])
            embed = discord.Embed(title=f"Category: {category} ({row[0]})",
                                  description=f"Guild: {guild} ({row[1]})\nEmote: {row[2]}",
                                  color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.set_footer(text="Active categories")

            embeds.append(embed)

        await msg.delete()
        await disputils.BotEmbedPaginator(ctx, embeds).run()

    # categories all takes no parameters
    #  gets all active and inactive modmail categories
    #  sends result on success, error on failure
    @categories.command()
    @is_admin()
    @commands.guild_only()
    async def all(self, ctx):
        msg = await ctx.send(embed=common_embed("Categories", "Retrieving all categories."))

        results = await self.db_conn.fetch("SELECT category_id, active, guild_id, emote_id \
                                            FROM modmail.categories")
        embeds = list()

        for row in results:
            guild = await self.bot.fetch_guild(row[2])
            category = await self.bot.fetch_channel(row[0])
            embed = discord.Embed(title=f"Category: {category} ({row[0]})",
                                  description=f"Guild: {guild} ({row[2]})\nEmote: {row[3]}\nActive: {row[1]}",
                                  color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.set_footer(text="All categories")

            embeds.append(embed)

        await msg.delete()
        await disputils.BotEmbedPaginator(ctx, embeds).run()

    @categories.error
    async def categories_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # category takes category_id int
    #  checks if category is existing
    #  gets information about the category
    #  sends result on success, error on failure
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def category(self, ctx, category_id: int) -> None:
        results = await self.db_conn.fetchrow("SELECT * \
                                               FROM modmail.categories \
                                               WHERE \
                                                  category_id=$1", category_id)
        if not results:
            await ctx.send(embed=common_embed("Category",
                                              f"Did not find category with category id {category_id}."))
            return

        guild = await self.bot.fetch_guild(results[3])
        category = await self.bot.fetch_channel(category_id)
        await ctx.send(embed=common_embed(f"Category: {category} ({category_id})",
                                          f"Guild: {guild} ({results[3]})\nEmote: {results[4]}\nActive: {results[2]}"))

    @category.error
    async def category_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help category`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help category`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # update_category_name takes category_id int
    #  checks if category is existing
    #  asks for confirmation
    #  updates category
    #  sends result on success, error on failure
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def update_category_name(self, ctx, category_id: int, new_name: str) -> None:
        category_result = await self.db_conn.fetchrow("SELECT category_name, emote_id \
                                                       FROM modmail.categories \
                                                       WHERE \
                                                           category_id=$1", category_id)

        if not category_result:
            await ctx.send(embed=common_embed("Update emote",
                                              "I do not recognize this category id. Did you make a typo?"))
            return

        success = await confirmation(self.bot, ctx, "Update category name",
                                     f"Are you sure you want to change category with name {category_result[0]} to name "
                                     f"{new_name}?", "update_category_name")

        if not success:
            return

        category_channel = await self.bot.fetch_channel(category_id)
        await category_channel.edit(name=new_name,
                                    reason=f"Command: update_category_name was run by {ctx.message.author.name}")

        await self.db_conn.execute("UPDATE modmail.categories \
                                    SET category_name=$1 \
                                    WHERE \
                                      category_id=$2", new_name, category_id)

    @update_category_name.error
    async def update_category_name_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help update_category_name`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help update_category_name`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")


def setup(bot):
    bot.add_cog(CategoriesCog(bot))
