from utils.checks import *
from utils.fetch_util import *
from utils.confirmation import *
from utils.title_and_desc import *
import typing
import discord
import disputils


class PermissionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = self.bot.db_conn

    # set_permissions takes category_id int, role_id discord.Role/int
    #  makes sure category is real and active, role is real
    #  checks if permission exists but is active => returns
    #  checks if permission exists but is inactive => confirmation to activate
    #  if neither, asks for confirmation and adds the permission
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def set_permissions(self, ctx, category_id: int, role: typing.Union[discord.Role, int]) -> None:
        if isinstance(role, discord.Role):
            role = role.id

        results_cat = await self.db_conn.fetchrow("SELECT * \
                                                   FROM modmail.categories \
                                                   WHERE \
                                                      active=TRUE AND \
                                                      category_id=$1", category_id)
        if not results_cat:
            await ctx.send(embed=common_embed("Set permissions",
                                              f"Did not find active category with category id {category_id}."))
            return

        if not await fetch_role(self.bot, role, results_cat[3]):
            await ctx.send(embed=common_embed("Set permissions", f"Could not find role with role id {role}"))

            return

        results = await self.db_conn.fetchrow("SELECT * \
                                               FROM modmail.permissions \
                                               WHERE \
                                                  category_id=$1 AND \
                                                  role_id=$2 ", category_id, role)
        if results:
            category = await self.bot.fetch_channel(results[0])
            if results[3]:
                await ctx.send(embed=common_embed("Set permissions",
                                                  f"Role: {results[1]} already has permissions in category {category} "
                                                  f"({category_id})."))
                return
            else:
                success = await confirmation(self.bot, ctx, "Set permissions",
                                             f"{results[1]} ({int(role)}) previously had access to {category} "
                                             f"({category_id}) but is set to inactive. Do you want to set role "
                                             f"{results[1]} to active for {category} ({category_id})?",
                                             "set_permissions")

                if not success:
                    return

                await self.db_conn.execute("UPDATE modmail.permissions \
                                            SET active=TRUE \
                                            WHERE \
                                              category_id=$1", category_id)

        guild = await self.bot.fetch_guild(results_cat[3])
        role = discord.utils.get(guild.roles, id=role)
        category = await self.bot.fetch_channel(category_id)

        success = await confirmation(self.bot, ctx, "Set permissions",
                                     f"Are you sure you want to give role {role.name} ({role.id}) permissions for "
                                     f"{category} ({category_id})?",
                                     "set_permissions")

        if not success:
            return

        await self.db_conn.execute("INSERT INTO modmail.permissions \
                                    (category_id, role_name, role_id, active) \
                                    VALUES($1, $2, $3, TRUE)", category_id, role.name, role.id)

        ch = self.bot.get_channel(category_id)
        await ch.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)

    @set_permissions.error
    async def set_permissions_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help set_permissions`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help set_permissions`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # permissions takes no parameters
    #  gets all active permissions
    #  sends result on success, error on failure
    @commands.group(invoke_without_command=True)
    @is_admin()
    @commands.guild_only()
    async def permissions(self, ctx) -> None:
        msg = await ctx.send(embed=common_embed("Permissions", "Retrieving active permissions."))

        results = await self.db_conn.fetch("SELECT * \
                                            FROM modmail.permissions \
                                            WHERE \
                                               active=TRUE")
        embeds = list()

        for row in results:
            category = await self.bot.fetch_channel(row[0])
            role = discord.utils.get(category.guild.roles, id=row[2])
            embed = discord.Embed(title=f"Category: {category} ({row[0]})",
                                  description=f"Guild: {category.guild} ({category.guild.id})\n"
                                              f"Role: {role.mention if category.guild.id == ctx.guild.id else role.name}"
                                              f"({row[2]})",
                                  color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.set_footer(text="Active permissions")

            embeds.append(embed)

        await msg.delete()
        await disputils.BotEmbedPaginator(ctx, embeds).run()

    # permissions all takes no parameters
    #  gets all active and inactive permissions
    #  sends result on success, error on failure
    @permissions.command()
    @is_admin()
    @commands.guild_only()
    async def all(self, ctx) -> None:
        msg = await ctx.send(embed=common_embed("Permissions", "Retrieving all permissions."))

        results = await self.db_conn.fetch("SELECT * \
                                            FROM modmail.permissions")
        embeds = list()

        for row in results:
            title, desc = await get_title_and_description(self.bot, row)

            embed = discord.Embed(title=title,
                                  description=desc,
                                  color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.set_footer(text="All permissions")

            embeds.append(embed)

        await msg.delete()
        await disputils.BotEmbedPaginator(ctx, embeds).run()

    @permissions.error
    async def permissions_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # category_permissions takes category_id int
    #  gets all active permissions for this category
    #  sends result on success, error on failure
    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def category_permissions(self, ctx, category_id: int) -> None:
        category_result = await self.db_conn.fetchrow("SELECT * \
                                                       FROM modmail.permissions \
                                                       WHERE \
                                                           category_id=$1", category_id)

        if not category_result:
            await ctx.send(embed=common_embed("Category permissions",
                                              "I do not recognize this category id or no permissions have been set "
                                              "for this category. Did you make a typo?"))
            return

        msg = await ctx.send(embed=common_embed("Category permissions", "Retrieving active permissions for category."))

        results = await self.db_conn.fetch("SELECT * \
                                            FROM modmail.permissions \
                                            WHERE \
                                               active=TRUE AND \
                                               category_id=$1", category_id)
        embeds = list()

        for row in results:
            category = await self.bot.fetch_channel(row[0])
            role = discord.utils.get(category.guild.roles, id=row[2])
            embed = discord.Embed(title=f"Category: {category} ({row[0]})",
                                  description=f"Guild: {category.guild} ({category.guild.id})\n"
                                              f"Role: {role.mention if category.guild.id==ctx.guild.id else role.name} "
                                              f"({row[2]})",
                                  color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.set_footer(text="Active permissions")

            embeds.append(embed)

        await msg.delete()
        await disputils.BotEmbedPaginator(ctx, embeds).run()

    @category_permissions.error
    async def category_permissions_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help "
                           f"category_permissions`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument. Please type `{self.bot.command_prefix}help "
                           f"category_permissions`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # activate_permission takes category_id int and role_id discord.Role/int
    #  makes sure category is real and inactive
    #  asks confirmation and updates the database
    @commands.command(aliases=['activate_permissions'])
    @is_admin()
    @commands.guild_only()
    async def activate_permission(self, ctx, category_id: int, role: typing.Union[discord.Role, int]) -> None:
        if isinstance(role, discord.Role):
            role = role.id

        results_perm = await self.db_conn.fetchrow("SELECT * \
                                                    FROM modmail.permissions \
                                                    WHERE \
                                                       category_id=$1 AND \
                                                       role_id=$2", category_id, role)
        if not results_perm:
            await ctx.send(embed=common_embed("Activate permissions",
                                              f"Did not find active permissions for category with category id "
                                              f"{category_id} and role with role id {role}."))
            return

        category = await self.bot.fetch_channel(category_id)

        if not isinstance(role, discord.Role):
            guild = await self.bot.fetch_guild(category.guild.id)
            role = discord.utils.get(guild.roles, id=role)

        if results_perm[3]:
            await ctx.send(embed=common_embed("Activate permissions",
                                              f"The permissions for role {results_perm[1]} ({results_perm[2]}) for "
                                              f"category {category} ({category_id}) are already active. "
                                              f"Did you mean `{self.bot.command_prefix}deactivate_permission "
                                              f"{category_id} {role}`?"))
            return

        success = await confirmation(self.bot, ctx, "Activate permissions",
                                     f"Are you sure you want to activate the permissions for role {results_perm[1]} "
                                     f"({results_perm[2]}) for category {category} ({category_id})?",
                                     "activate_permissions")

        if not success:
            return

        await self.db_conn.execute("UPDATE modmail.permissions \
                                    SET active=TRUE \
                                    WHERE \
                                      category_id=$1", category_id)

        ch = self.bot.get_channel(category_id)
        await ch.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)

    @activate_permission.error
    async def activate_permission_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help activate_permission`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help activate_permission`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")

    # deactivate_permission takes category_id int and role_id discord.Role/int
    #  makes sure category is real and active
    #  asks confirmation and updates the database
    @commands.command(aliases=['delete_permissions', 'remove_permissions', 'deactivate_permissions'])
    @is_admin()
    @commands.guild_only()
    async def deactivate_permission(self, ctx, category_id: int, role: typing.Union[discord.Role, int]) -> None:
        results_perm = await self.db_conn.fetchrow("SELECT * \
                                                    FROM modmail.permissions \
                                                    WHERE \
                                                       category_id=$1 AND \
                                                       role_id=$2", category_id, role)
        if not results_perm:
            await ctx.send(embed=common_embed("Deactivate permissions",
                                              "Did not find active permissions for category with category id "
                                              f"{category_id} and role with role id {role}."))
            return

        category = await self.bot.fetch_channel(category_id)

        if not isinstance(role, discord.Role):
            guild = await self.bot.fetch_guild(category.guild.id)
            role = discord.utils.get(guild.roles, id=role)

        if not results_perm[3]:
            await ctx.send(embed=common_embed("Deactivate permissions",
                                              f"The permissions for role {results_perm[1]} ({results_perm[2]}) for "
                                              f"category {category} ({category_id}) are already inactive. "
                                              f"Did you mean `{self.bot.command_prefix}activate_permission "
                                              f"{category_id} {role}`?"))
            return

        success = await confirmation(self.bot, ctx, "Deactivate permissions",
                                     f"Are you sure you want to deactivate the permissions for role {results_perm[1]} "
                                     f"({results_perm[2]}) for category {category} ({category_id})?",
                                     "deactivate_permissions")

        if not success:
            return

        await self.db_conn.execute("UPDATE modmail.permissions \
                                    SET active=FALSE \
                                    WHERE \
                                      category_id=$1", category_id)

        ch = self.bot.get_channel(category_id)
        await ch.set_permissions(role, read_messages=False, send_messages=False, read_message_history=False)

    @deactivate_permission.error
    async def deactivate_permission_error(self, ctx, err) -> None:
        if isinstance(err, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to run this command")
        elif isinstance(err, commands.BadArgument):
            await ctx.send(f"Bad argument passed. Please type `{self.bot.command_prefix}help deactivate_permission`.")
        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument. Please type `{self.bot.command_prefix}help deactivate_permission`.")
        else:
            await ctx.send(f"Unknown error occurred.\n{str(err)}")


def setup(bot):
    bot.add_cog(PermissionsCog(bot))
