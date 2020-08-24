from utils.category_selector import *
from discord.ext import commands
from utils.common_embed import *


class messageHandlingTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn
        self.yellow = 0xE8D90C
        self.green = 0x7CFC00
        self.red = 0xe50000

    # Listens for user private messages
    #  if not in a conversation creates conversation => asks for desired category with emotes
    #  if user in conversation sends message to conversation
    #  Sends confirmation on success, raises error on failure
    @commands.Cog.listener(name="on_message")
    async def dm_message_listener(self, message: discord.Message) -> None:
        if (message.content.startswith(self.bot.command_prefix)) or (message.author == self.bot.user):
            return

        if message.guild is not None:
            active_channels = await self.db_conn.fetch("SELECT channel_id \
                                                        FROM modmail.conversations \
                                                        WHERE \
                                                           active=true")

            active_channel_list = [channel[0] for channel in active_channels]

            if message.channel.id in active_channel_list:
                conv_id = await self.db_conn.fetchrow("SELECT conversation_id \
                                                       FROM modmail.conversations \
                                                       WHERE \
                                                           channel_id=$1 AND \
                                                           active=true",
                                                      message.channel.id)

                await self.db_conn.execute("INSERT INTO modmail.all_messages_attachments \
                                            (message_id, message, author_id, conversation_id, made_by_mod) \
                                            VALUES ($1, $2, $3, $4, true)",
                                           message.id, message.content, message.author.id, conv_id[0])

                if message.attachments:
                    attachment_object = await message.attachments[0].read()
                    await self.db_conn.execute("UPDATE modmail.all_messages_attachments \
                                                SET attachment=$1 \
                                                WHERE \
                                                    message_id=$2", attachment_object, message.id)

            return

        check_muted = await self.db_conn.fetchrow("SELECT active \
                                                   FROM modmail.muted \
                                                   WHERE \
                                                        user_id=$1 AND \
                                                        active=true", message.author.id)
        if check_muted:
            return

        conv = await self.db_conn.fetchrow("SELECT conversation_id, channel_id \
                                            FROM modmail.conversations \
                                            WHERE \
                                                user_id=$1 AND \
                                                active=true",
                                           message.author.id)
        if not conv:
            category, guild = await category_selector.start_embed(self.bot, message.channel, message.author) or (
                None, None)

            if category is None:
                return

            channel = await guild.create_text_channel(f"{message.author.name}-{message.author.discriminator}",
                                                      category=category)
            await channel.edit(topic=f"{message.author.id}")

            past_threads = await self.db_conn.fetch("SELECT * \
                                                     FROM modmail.conversations \
                                                     WHERE \
                                                        user_id=$1 AND \
                                                        active=false",
                                                    message.author.id)
            check = False
            if int(guild.id) == int(self.bot.conf.get('global', 'main_server_id')):
                check = True

            if check:
                try:
                    user = guild.get_member(message.author.id)
                    created_ago = datetime.datetime.now() - user.created_at
                    joined_ago = datetime.datetime.now() - user.joined_at
                    chnl_embed_msg = f"{user.mention} was created {created_ago.days} days ago, " \
                                     f"joined {joined_ago.days} days ago"
                except AttributeError:
                    check = False

            if not check:
                user = message.author
                created_ago = datetime.datetime.now() - user.created_at
                chnl_embed_msg = f"{user.mention} was created {created_ago.days} days ago, "

            chnl_embed_msg += f" with **{'no' if len(past_threads) == 0 else len(past_threads)}** past threads"

            chnl_embed = common_embed(f"{message.author.id}", chnl_embed_msg, color=0x7289da)
            chnl_embed.set_author(name=str(user), icon_url=user.avatar_url)

            if check:
                roles = " ".join([role.mention for role in user.roles if not role.is_default()])
            else:
                roles = ""
            chnl_embed.add_field(name="Roles", value=roles if roles else "No Roles")
            await channel.send(embed=chnl_embed)

            thread_embed = common_embed("", message.content, color=self.yellow)
            thread_embed.set_author(name=message.author, icon_url=message.author.avatar_url)

            for attachment in message.attachments:
                thread_embed.add_field(name=f"File upload ({len(message.attachments)})",
                                       value=f"[{attachment.filename}]({attachment.url})")

            thread_embed.set_footer(text=f"Message ID: {message.id}")
            thread_msg = await channel.send(embed=thread_embed)

            await self.db_conn.execute("INSERT INTO modmail.conversations \
                                        (creation_date, user_id, active, channel_id, category_id) \
                                        VALUES (now(), $1, true, $2, $3)",
                                       message.author.id, channel.id, category.id)

            conv_id = await self.db_conn.fetchrow("SELECT conversation_id \
                                                   FROM modmail.conversations \
                                                   WHERE \
                                                        channel_id=$1", channel.id)

            await self.db_conn.execute("INSERT INTO modmail.messages \
                                        (message_id, message, author_id, conversation_id, other_side_message_id, \
                                         made_by_mod) \
                                        VALUES ($1, $2, $3, $4, $5, false)",
                                       message.id, message.content, message.author.id, conv_id[0], thread_msg.id)

            await self.db_conn.execute("INSERT INTO modmail.all_messages_attachments \
                                        (message_id, message, author_id, conversation_id, made_by_mod) \
                                        VALUES ($1, $2, $3, $4, false)",
                                       message.id, message.content, message.author.id, conv_id[0])

            usr_embed = common_embed("Message sent",
                                     f"> {message.content} \n\n *if this isn't correct you can change it with "
                                     f"{self.bot.command_prefix}edit*",
                                     color=self.green)
            usr_embed.set_author(name=message.author, icon_url=message.author.avatar_url)

            for attachment in message.attachments:
                usr_embed.add_field(name=f"File upload ({len(message.attachments)})",
                                    value=f"[{attachment.filename}]({attachment.url})")

            usr_embed.set_footer(text=f"Message ID: {message.id}")
            await message.channel.send(embed=usr_embed)

        else:
            channel = await self.bot.fetch_channel(conv[1])

            thread_embed = common_embed("", message.content, color=self.yellow)
            thread_embed.set_author(name=message.author, icon_url=message.author.avatar_url)

            for attachment in message.attachments:
                thread_embed.add_field(name=f"File upload ({len(message.attachments)})",
                                       value=f"[{attachment.filename}]({attachment.url})")
            thread_embed.set_footer(text=f"Message ID: {message.id}")
            thread_msg = await channel.send(embed=thread_embed)

            usr_embed = common_embed("Message sent",
                                     f"> {message.content}\n\n *if this isn't correct you can change it with "
                                     f"{self.bot.command_prefix}edit*",
                                     color=self.green)
            usr_embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            for attachment in message.attachments:
                usr_embed.add_field(name=f"File upload ({len(message.attachments)})",
                                    value=f"[{attachment.filename}]({attachment.url})")
            usr_embed.set_footer(text=f"Message ID: {message.id}")
            await message.channel.send(embed=usr_embed)

            await self.db_conn.execute("INSERT INTO modmail.messages \
                                        (message_id, message, author_id, conversation_id, other_side_message_id, \
                                         made_by_mod) \
                                        VALUES ($1, $2, $3, $4, $5, false)",
                                       message.id, message.content, message.author.id, conv[0], thread_msg.id)

            await self.db_conn.execute("INSERT INTO modmail.all_messages_attachments \
                                        (message_id, message, author_id, conversation_id, made_by_mod) \
                                        VALUES ($1, $2, $3, $4, false)",
                                       message.id, message.content, message.author.id, conv[0])

        if message.attachments:
            attachment_object = await message.attachments[0].read()
            await self.db_conn.execute("UPDATE modmail.all_messages_attachments \
                                        SET attachment=$1 \
                                        WHERE \
                                            message_id=$2", attachment_object, message.id)

    # Listens for deleted messages
    #   If user deletes message => edits message in conversation to show it was deleted
    #   Fetches message content from database to account for edit messages
    #   Returns confirmation on success, raises error on failure
    @commands.Cog.listener(name="on_message_delete")
    async def dm_delete_listener(self, message: discord.Message) -> None:
        if message.guild is None:
            conv = await self.db_conn.fetchrow("SELECT conversation_id, channel_id, message_id \
                                                FROM modmail.conversations \
                                                WHERE \
                                                    user_id=$1 AND \
                                                    active=true",
                                               message.author.id)
            if conv:
                db_msg = await self.db_conn.fetchrow("SELECT other_side_message_id, message \
                                                      FROM modmail.messages \
                                                      WHERE \
                                                        message_id=$1 AND \
                                                        conversation_id=$2",
                                                     message.id, conv[0])

                thread_channel = await self.bot.fetch_channel(conv[1])
                thread_msg = await thread_channel.fetch_message(db_msg[0])

                thread_embed = common_embed("", db_msg[1], color=self.red)
                thread_embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                thread_embed.set_footer(text=f"Message ID: {message.id} (deleted)")

                await thread_msg.edit(embed=thread_embed)

                usr_msg = await message.author.dm_channel.fetch_message(conv[2])
                usr_embed = common_embed("Message deleted",
                                         f"> {message.content}",
                                         color=self.red)

                usr_embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                usr_embed.set_footer(text=f"Message ID: {message.id}")

                await usr_msg.edit(embed=usr_embed)
                await self.db_conn.execute("UPDATE modmail.messages \
                                            SET deleted=true \
                                            WHERE \
                                                message_id=$1", message.id)


def setup(bot):
    bot.add_cog(messageHandlingTasks(bot))
