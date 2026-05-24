import discord
from discord.ext import commands
from discord import app_commands
from src.db import client as db_client

class CustomCommandsCog(commands.Cog, name="Custom Commands"):
    """Manage custom commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="cc", description="Custom commands management.", fallback="help")
    @commands.has_permissions(manage_guild=True)
    async def cc_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @cc_group.command(name="add", description="Add a new custom command.")
    @app_commands.describe(trigger="The trigger word", response="The response text")
    async def cc_add(self, ctx: commands.Context, trigger: str, *, response: str):
        trigger = trigger.lower()
        try:
            data = {
                "guild_id": str(ctx.guild.id),
                "trigger_word": trigger,
                "response_text": response
            }
            res = db_client.supabase.table("custom_commands").upsert(data, on_conflict="guild_id,trigger_word").execute()
            if res.data:
                db_client.clear_guild_cache(str(ctx.guild.id))
                await ctx.send(embed=discord.Embed(description=f"✅ Added custom command: `{trigger}`", color=discord.Color.green()))
            else:
                await ctx.send("Failed to add custom command.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @cc_group.command(name="remove", description="Remove a custom command.")
    @app_commands.describe(trigger="The trigger word")
    async def cc_remove(self, ctx: commands.Context, trigger: str):
        trigger = trigger.lower()
        try:
            res = db_client.supabase.table("custom_commands").delete().eq("guild_id", str(ctx.guild.id)).eq("trigger_word", trigger).execute()
            if res.data:
                db_client.clear_guild_cache(str(ctx.guild.id))
                await ctx.send(embed=discord.Embed(description=f"✅ Removed custom command: `{trigger}`", color=discord.Color.green()))
            else:
                await ctx.send("Custom command not found.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @cc_group.command(name="list", description="List all custom commands.")
    async def cc_list(self, ctx: commands.Context):
        try:
            res = db_client.supabase.table("custom_commands").select("trigger_word").eq("guild_id", str(ctx.guild.id)).execute()
            if not res.data:
                return await ctx.send("No custom commands found for this server.")
            
            commands_list = ", ".join([f"`{row['trigger_word']}`" for row in res.data])
            embed = discord.Embed(title="Custom Commands", description=commands_list, color=0x3498DB)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        trigger = message.content.lower().split(" ")[0]
        try:
            custom_cmds = db_client.get_custom_commands(str(message.guild.id))
            if trigger in custom_cmds:
                cmd_data = custom_cmds[trigger]
                permission_level = cmd_data.get("permission_level", "Everyone")
                
                # Check permissions
                if permission_level and permission_level != "Everyone":
                    author_role_ids = [str(r.id) for r in message.author.roles]
                    author_role_names = [r.name.lower() for r in message.author.roles]
                    if (permission_level not in author_role_ids) and (permission_level.lower() not in author_role_names):
                        return  # User does not have the required role
                
                response_text = cmd_data.get("response_text", "")
                image_url = cmd_data.get("image_url")
                gif_url = cmd_data.get("gif_url")
                
                # Build embeds for images and gifs
                embeds = []
                if image_url:
                    img_emb = discord.Embed(color=0x0affe4)
                    img_emb.set_image(url=image_url)
                    embeds.append(img_emb)
                if gif_url:
                    gif_emb = discord.Embed(color=0x0affe4)
                    gif_emb.set_image(url=gif_url)
                    embeds.append(gif_emb)
                
                if embeds:
                    if response_text:
                        embeds[0].description = response_text
                    await message.channel.send(embeds=embeds)
                else:
                    if response_text:
                        await message.channel.send(response_text)
        except Exception:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomCommandsCog(bot))
