from discord.ext import commands
from utils.common_embed import *


class memberGuildLeaveJoinTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn

    # Checks if member has open conversation
    #  returns channel id or None
    async def member_has_conversation(self, member: discord.Member):
        active_channels = await self.db_conn.fetch("SELECT channel_id \
                                                    FROM modmail.conversations \
                                                    WHERE \
                                                       active=true AND \
                                                       user_id=$1", member.id)

        return active_channels

    # Listens for user who join the guild
    @commands.Cog.listener(name="on_member_join")
    async def member_join_listener(self, member: discord.Member) -> None:
        channel_id = await self.member_has_conversation(member=member)
        if (channel_id is not []) and (channel_id is not None) and (len(channel_id) > 0):
            if (channel_id[0] is not None) and (channel_id[0] is not "") and (len(channel_id[0]) > 0):
                if (channel_id[0][0] is not "") and (channel_id[0][0] is not None):
                    ch = await self.bot.fetch_channel(channel_id[0][0])
                    await ch.send(embed=common_embed("User joined the server.", "User joined the server."))

    # Listens for user who leaves the guild
    @commands.Cog.listener(name="on_member_remove")
    async def member_leave_listener(self, member: discord.Member) -> None:
        channel_id = await self.member_has_conversation(member=member)
        if (channel_id is not []) and (channel_id is not None) and (len(channel_id) > 0):
            if (channel_id[0] is not None) and (channel_id[0] is not "") and (len(channel_id[0]) > 0):
                if (channel_id[0][0] is not "") and (channel_id[0][0] is not None):
                    ch = await self.bot.fetch_channel(channel_id[0][0])
                    await ch.send(embed=common_embed("User left the server.", "User left the server."))


def setup(bot):
    bot.add_cog(memberGuildLeaveJoinTask(bot))
