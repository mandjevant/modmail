import asyncio
import pytz
import typing
import disputils
from asyncpg import ForeignKeyViolationError
from natural.date import duration
from utils.checks import *
from utils.reply import *
from tasks.message_handling import category_selector


class ModmailCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn
        self.conf = bot.conf
        self.yellow = 0xE8D90C
        self.green = 0x7CFC00

    # Reply takes a text of max 2048 characters
    #  replies to modmail with the inputted text
    #  sends reply on success, error on failure
    @commands.command(aliases=['r'])
    @commands.guild_only()
    @has_access()
    async def reply(self, ctx, *, message: typing.Optional[str]) -> None:
        if message is None and not ctx.message.attachments:
            raise commands.MissingRequiredArgument

        if message is not None and (len(message) > 2048):
            await ctx.send(embed=common_embed("Modmail Reply",
                                              "Sorry this message is over 2048 characters, please reduce the "
                                              "character count"))
            return

        conv = await self.db_conn.fetchrow("SELECT conversation_id, user_id \
                                            FROM modmail.conversations \
                                            WHERE \
                                                channel_id=$1 AND active=true",
                                           ctx.channel.id)

        if not conv:
            await ctx.send(embed=common_embed("Modmail Reply",
                                              f"You are currently not in a modmail thread, if you want to create one "
                                              f"look at `{ctx.prefix}help create`"))
            return

        await reply(self.bot, ctx, self.db_conn, conv[1], f'{message} \n', conv[0], attachments=ctx.message.attachments)

    @reply.error
    async def reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # Reply takes a text of max 2048 characters
    #  replies to modmail with the inputted text anonymously
    #  sends reply on success, error on failure
    @commands.command(aliases=['ar'])
    @has_access()
    @commands.guild_only()
    async def anonymous_reply(self, ctx, *, message: typing.Optional[str]) -> None:
        if message is None and not ctx.message.attachments:
            raise commands.MissingRequiredArgument

        if message is not None and (len(message) > 2048):
            await ctx.send(embed=common_embed("Modmail Reply",
                                              "Sorry this message is over 2048 characters, please reduce the "
                                              "character count"))
            return

        conv = await self.db_conn.fetchrow("SELECT conversation_id, user_id \
                                            FROM modmail.conversations \
                                            WHERE \
                                               channel_id=$1 AND \
                                               active=true",
                                           ctx.channel.id)

        if not conv:
            await ctx.send(embed=common_embed("Modmail Reply",
                                              f"You are currently not in a modmail thread, if you want to create one "
                                              f"look at `{ctx.prefix}help create`"))
            return

        await reply(self.bot, ctx, self.db_conn, conv[1], message, conv[0], anon=True,
                    attachments=ctx.message.attachments)

    @anonymous_reply.error
    async def anonymous_reply_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help anonymous_reply`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help anonymous_reply`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # create takes user discord.Member, int and category int, str.
    #  If category string => Fetches category from string.
    #  Creates modmail thread and notifies the user about it.
    #  Creates channel on success, error on failure.
    @commands.command(aliases=['contact', 'newthread', 'new_thread'])
    @has_access()
    @commands.guild_only()
    async def create(self, ctx, user: typing.Union[discord.Member, int]) -> None:
        main_guild = await self.bot.fetch_guild(self.conf.get('global', 'main_server_id'))

        if isinstance(user, int):
            user = main_guild.get_member(user)

        if not user:
            await ctx.send(embed=common_embed("Create conversation",
                                              "Unable to find that user, please check the id and try again"))
            return

        category, guild = await category_selector.start_embed(self.bot, ctx.channel, ctx.author, True) or (None, None)

        if category or guild is None:
            return

        channel = await guild.create_text_channel(name=f'{user.name}-{user.discriminator}', category=category)

        try:
            await self.db_conn.execute("INSERT INTO modmail.conversations \
                                        (creation_date, user_id, active, channel_id, category_id) \
                                        VALUES (now(), $1, true, $2, $3)",
                                       user.id, channel.id, category.id)
        except ForeignKeyViolationError:
            await ctx.send(embed=common_embed("Create conversation",
                                              "The category that was provided is not a valid modmail category, "
                                              "please check your id or name and try again"))
            await channel.delete(reason="Thread Closed")
            return

        past_threads = await self.db_conn.fetch("SELECT * \
                                                 FROM modmail.conversations \
                                                 WHERE \
                                                    user_id=$1 AND \
                                                    active=false",
                                                user.id)
        created_ago, joined_ago = datetime.datetime.now() - user.created_at, datetime.datetime.now() - user.joined_at

        chnl_embed = common_embed("", f"{user.mention} was created {created_ago.days} days ago, "
                                      f"joined {joined_ago.days} days ago"
                                      f" with **{'no' if len(past_threads) == 0 else len(past_threads)}** past threads",
                                  color=0x7289da)
        chnl_embed.set_author(name=str(user), icon_url=user.avatar_url)
        roles = " ".join([role.mention for role in user.roles if role.id != main_guild.id])
        chnl_embed.add_field(name="Roles", value=roles if roles else "No Roles")
        await channel.send(embed=chnl_embed)

        await channel.send(embed=common_embed("Created conversation",
                                              f"Thread created by {ctx.author.mention} for {user.mention}"))

        try:
            await user.send(embed=common_embed("Conversation created", f"A modmail was created to contact {user}"))

        except discord.Forbidden:
            await channel.send(embed=common_embed("Create conversation",
                                                  "The user has dm's disabled so I can't reach out\n"
                                                  "This thread will get deleted in 15 seconds..."))
            await asyncio.sleep(15)
            await self.db_conn.execute("UPDATE modmail.conversations \
                                        SET closing_date=now(), active=false \
                                        WHERE \
                                          channel_id=$1",
                                       channel.id)
            await channel.delete(reason="Thread Closed")

        else:
            await ctx.message.add_reaction('✅')
            await asyncio.sleep(10)
            await ctx.message.delete()

    @create.error
    async def create_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help create`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help create`.")
        else:
            raise err
            # await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # Close takes no arguments
    #  closes the modmail thread aka channel
    #  sends confirmation on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def close(self, ctx) -> None:
        conv = await self.db_conn.fetchrow("SELECT user_id \
                                            FROM modmail.conversations \
                                            WHERE \
                                                channel_id=$1",
                                           ctx.channel.id)
        if not conv:
            await ctx.send(embed=common_embed("Close conversation",
                                              "You're in a invalid channel, please check if you're in a "
                                              "conversation channel"))
            return

        user = await self.bot.fetch_user(user_id=conv[0])
        try:
            await user.send(embed=common_embed("Conversation closed",
                                               "The conversation was closed, we hope that we were able to help you!"))
        except discord.Forbidden:
            await ctx.send(embed=common_embed("Conversation closed",
                                              "The user disabled dm's so no message's arrived"))
        finally:
            await self.db_conn.execute("UPDATE modmail.conversations \
                                        SET closing_date=now(), active=false \
                                        WHERE \
                                            channel_id=$1",
                                       ctx.channel.id)
            await ctx.send(embed=common_embed("Conversation closed", "This channel will get deleted in 10 seconds..."))
            await asyncio.sleep(10)

        await ctx.channel.delete(reason="Thread Closed")

    @close.error
    async def close_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # edit takes message str max size of 2048 characters
    #  Checks on what side it is on
    #  If on mod side => edits the most recent message made by mod
    #  If on user side => Edits the most recent message and notifies the mods about it and shows original state
    #  Edits message on success error on failure.
    @commands.command()
    async def edit(self, ctx, *, message: str) -> None:
        if ctx.guild is None:
            results = await self.db_conn.fetchrow("SELECT messages.message_id, messages.other_side_message_id, \
                                                          conversations.user_id, conversations.channel_id, \
                                                          messages.message \
                                                   FROM modmail.messages \
                                                   INNER JOIN modmail.conversations \
                                                   ON messages.conversation_id = conversations.conversation_id \
                                                   WHERE conversations.user_id=$1 AND messages.made_by_mod = false AND messages.deleted = false \
                                                   ORDER BY messages.created_at DESC \
                                                   LIMIT 1", ctx.author.id)
            if not results:
                await ctx.send(embed=common_embed("Edit message", "There's no message made in this thread yet"))
                return

            mod_chnl = await self.bot.fetch_channel(results[3])

            mod_msg = await mod_chnl.fetch_message(results[1])

            usr_embed = common_embed("Successfully edited the message", message, color=self.yellow)
            usr_embed.add_field(name="Original Message:", value=results[4])
            usr_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            usr_embed.set_footer(text=f"Message ID: {results[0]} (edited)")

            thread_embed = common_embed("", message, color=self.green)
            thread_embed.add_field(name="Edited, original message:", value=results[4])
            thread_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            thread_embed.set_footer(text=f"Message ID: {results[0]} (edited)")

            await ctx.send(embed=usr_embed)
            await mod_msg.edit(embed=thread_embed)

            await self.db_conn.execute("UPDATE modmail.messages \
                                        SET message=$1 \
                                        WHERE \
                                            message_id=$2",
                                       message, results[0])

            await ctx.message.add_reaction('✅')

        else:
            results = await self.db_conn.fetchrow("SELECT messages.message_id, messages.other_side_message_id, \
                                                          conversations.user_id \
                                                   FROM modmail.messages \
                                                   INNER JOIN modmail.conversations \
                                                   ON messages.conversation_id = conversations.conversation_id \
                                                   WHERE \
                                                      conversations.channel_id = $1 AND \
                                                      messages.made_by_mod = true AND \
                                                      deleted = false AND \
                                                      messages.author_id = $2 \
                                                   ORDER BY messages.created_at DESC \
                                                   LIMIT 1",
                                                  ctx.channel.id, ctx.author.id)
            if not results:
                await ctx.send(embed=common_embed("Edit message", "There's no message made in this thread yet"))
                return

            usr = await self.bot.fetch_user(results[2])

            mod_msg = await ctx.channel.fetch_message(results[0])
            usr_msg = await usr.dm_channel.fetch_message(results[1])

            usr_embed = common_embed('', message, color=self.yellow)
            usr_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            usr_embed.set_footer(text=ctx.author.roles[-1].name)

            thread_embed = common_embed('', message, color=self.green)
            thread_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            thread_embed.set_footer(text=ctx.author.roles[-1].name)

            await usr_msg.edit(embed=usr_embed)
            await mod_msg.edit(embed=thread_embed)

            await self.db_conn.execute("UPDATE modmail.messages \
                                        SET message=$1 \
                                        WHERE \
                                            message_id=$2",
                                       message, results[0])

            await ctx.message.add_reaction('✅')

    @edit.error
    async def edit_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help edit`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help edit`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # Delete takes no arguments.
    #  Only available for mods, user runs on event
    #  If there is a message to delete => Deletes the message on user and mod side
    #  Returns nothing on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def delete(self, ctx) -> None:
        results = await self.db_conn.fetchrow("SELECT messages.message_id, messages.other_side_message_id, \
                                                      conversations.user_id \
                                               FROM modmail.messages \
                                               INNER JOIN modmail.conversations \
                                               ON messages.conversation_id = conversations.conversation_id \
                                               WHERE \
                                                    conversations.channel_id = $1 AND \
                                                    messages.made_by_mod = true AND \
                                                    deleted = false \
                                               ORDER BY messages.created_at DESC \
                                               LIMIT 1", ctx.channel.id)
        if not results:
            await ctx.send(embed=common_embed("Delete message", "There's no message made by mods in this thread yet"))
            return

        usr = await self.bot.fetch_user(results[2])

        mod_msg: discord.Message = await ctx.channel.fetch_message(results[0])
        usr_msg: discord.Message = await usr.dm_channel.fetch_message(results[1])

        await mod_msg.delete()
        await usr_msg.delete()
        await self.db_conn.execute("UPDATE modmail.messages \
                                    SET deleted=true \
                                    WHERE \
                                        message_id=$1", results[0])

        await ctx.message.add_reaction('✅')

    @delete.error
    async def delete_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # forward takes category int, str
    #  If category int => checks if valid returns error on failure
    #  If category str => fetches category id from db with the name
    #  Forwards the conversation to the selected category
    #  Sends every previous message in new thread and deletes old channel
    #  Returns confirmation on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def forward(self, ctx, category: typing.Union[int, str]) -> None:
        if isinstance(category, int):
            if ctx.channel.category.id == category:
                await ctx.send(embed=common_embed("Forward conversation", "The conversation is already in that thread"))
                return

            cat_db = await self.db_conn.fetchrow("SELECT category_id, guild_id \
                                                  FROM modmail.categories \
                                                  WHERE \
                                                    category_id = $1",
                                                 category)
            if not cat_db:
                await ctx.send(embed=common_embed("Forward conversation",
                                                  "I can't find the category related to that id please check if its "
                                                  "correct"))
                return

        else:
            if ctx.channel.category.name == category:
                await ctx.send(embed=common_embed("Forward conversation", "The conversation is already in that thread"))
                return

            cat_db = await self.db_conn.fetchrow("SELECT category_id, guild_id \
                                                  FROM modmail.categories \
                                                  WHERE \
                                                    lower(category_name) = lower($1)",
                                                 category)
            if not cat_db:
                await ctx.send(embed=common_embed("Create conversation",
                                                  "Unable to fetch that category please check spelling or use the id"))
                return
        usr_db = await self.db_conn.fetchrow("SELECT user_id, conversation_id \
                                              FROM modmail.conversations \
                                              WHERE \
                                                channel_id=$1", ctx.channel.id)

        guild = self.bot.get_guild(cat_db[1]) if not ctx.guild.id == cat_db[1] else ctx.guild
        category = await self.bot.fetch_channel(cat_db[0])
        user = await self.bot.fetch_user(usr_db[0])

        channel = await guild.create_text_channel(name=f"{user.name}-{user.discriminator}", category=category)

        past_threads = await self.db_conn.fetch("SELECT conversation_id \
                                                 FROM modmail.conversations \
                                                 WHERE \
                                                    user_id=$1 AND \
                                                    active=false",
                                                user.id)

        created_ago = datetime.datetime.now() - user.created_at

        await channel.send(embed=common_embed("", f"{user.mention} was created {created_ago.days} days ago"
                                                  f" with **{'no' if len(past_threads) == 0 else len(past_threads)}** "
                                                  f"past threads"))
        await channel.send(embed=common_embed("Forwarded conversation",
                                              f"Conversation forwarded by {ctx.author.mention} from "
                                              f"{ctx.channel.category.name}"))
        messages = await self.db_conn.fetch("SELECT message, made_by_mod, author_id, message_id \
                                             FROM modmail.messages \
                                             WHERE \
                                                conversation_id=$1 AND \
                                                deleted=false",
                                            usr_db[1])

        for row in messages:
            author = await self.bot.fetch_user(row[2])

            thread_embed = common_embed("", row[0], color=self.green if row[1] else self.yellow)
            thread_embed.set_author(name=str(author), icon_url=author.avatar_url)
            thread_embed.set_footer(text="Forwarded message")
            msg = await channel.send(embed=thread_embed)

            await self.db_conn.execute("UPDATE modmail.messages \
                                        SET message_id=$1 \
                                        WHERE \
                                            message_id=$2",
                                       msg.id, row[3])

        await self.db_conn.execute("UPDATE modmail.conversations \
                                    SET channel_id = $1 \
                                    WHERE \
                                        conversation_id=$2",
                                   channel.id, usr_db[1])

        await user.send(embed=common_embed("Conversation forward", f"You were forwarded to {channel.category.name}"))
        await ctx.send(embed=common_embed("Conversation forward",
                                          "The conversation was successfully forwarded this channel will get deleted "
                                          "in 10 seconds"))
        await asyncio.sleep(10)
        await ctx.channel.delete()

    @forward.error
    async def forward_error(self, ctx, err: any) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help forward`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help forward`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # Logs takes optional user discord.Member, int
    #  displays the discord user's past modmails in pages
    #  sends paginator(s) on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def logs(self, ctx: commands.Context, user: typing.Optional[typing.Union[discord.Member, int]]) -> None:
        if user is None:
            result = await self.db_conn.fetchrow("SELECT user_id \
                                                  FROM modmail.conversations \
                                                  WHERE \
                                                     channel_id = $1",
                                                 ctx.channel.id)
            if not result:
                await ctx.send(
                    embed=common_embed(title="Not Found",
                                       description="Unable to locate modmail thread, please specify the id"))
                return

            user = await self.bot.fetch_user(result[0])

        else:
            if isinstance(user, int):
                user = await self.bot.fetch_user(user)

            if not user:
                await ctx.send(embed=common_embed("Create conversation",
                                                  "Unable to find that user, please check the id and try again"))
                return

        embeds = list()

        conversations = await self.db_conn.fetch("SELECT conversations.conversation_id, conversations.created_at,\
                                                         conversations.closing_date, categories.category_name, \
                                                         categories.category_id \
                                                  FROM modmail.conversations \
                                                  INNER JOIN modmail.categories \
                                                  ON conversations.category_id = categories.category_id \
                                                  WHERE \
                                                    conversations.active=false AND \
                                                    conversations.user_id=$1 \
                                                  ORDER BY created_at DESC", user.id)
        if conversations:
            async with ctx.typing():
                for row in conversations:
                    embed = common_embed("", f"ID: {row[0]}")
                    embed.set_author(name=f"Total Results Found ({len(conversations)}) - {user}",
                                     icon_url=user.avatar_url)
                    embed.add_field(name="Created", value=duration(row[1], now=datetime.datetime.now(pytz.utc)))
                    embed.add_field(name="Closed", value=duration(row[1], now=datetime.datetime.now(pytz.utc)))
                    embed.add_field(name="Category", value=f"{row[3].capitalize()} ({row[4]})")

                    messages = await self.db_conn.fetch("SELECT message, author_id, deleted, made_by_mod \
                                                         FROM modmail.messages \
                                                         WHERE \
                                                            conversation_id=$1 \
                                                         ORDER BY created_at", row[0])
                    embed_messages = list()

                    for index, message in enumerate(messages, 1):
                        if message[2]:
                            embed_messages.append(
                                f'[{index}] - ~~{message[0]}~~ ~ <@{message[1]}> {"(mod)" if message[3] else ""}')
                        else:
                            embed_messages.append(
                                f'[{index}] - {message[0]} ~ <@{message[1]}> {"(mod)" if message[3] else ""}')

                    embed.add_field(name="Messages:",
                                    value="\n".join(embed_messages if embed_messages else ["No messages"]),
                                    inline=False)
                    embeds.append(embed)

            await disputils.BotEmbedPaginator(ctx, embeds).run()
        else:
            await ctx.send(embed=common_embed('Logs', f'No prior logs found for {user}'))

    @logs.error
    async def logs_error(self, ctx, err: any):
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help logs`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help logs`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")


def setup(bot):
    bot.add_cog(ModmailCog(bot))
