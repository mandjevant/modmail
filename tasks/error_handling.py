import copy

import discord
from discord.ext import commands


class error_handling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = bot.conf

    async def send_help(self, ctx, message: str) -> None:
        msg = copy.copy(ctx.message)
        msg.channel = ctx.channel
        msg.content = ctx.prefix + 'help ' + ctx.command.name
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await new_ctx.send(message)
        await self.bot.invoke(new_ctx)

    @commands.Cog.listener(name="on_command_error")
    async def command_error_handling(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_help(ctx, "Missing required argument(s)")

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")

        elif isinstance(error, commands.BadArgument):
            await self.send_help(ctx, message="Bad argument passed")

        else:
            await ctx.send(f"Unknown error occurred.\n{str(error)}")
            if self.conf.get('global', 'production').lower() != "true":
                raise error


def setup(bot):
    bot.add_cog(error_handling(bot))
