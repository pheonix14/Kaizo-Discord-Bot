import discord
from discord.ext import commands
from discord import app_commands
import json
import io

class BuilderHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "🏗️ KAIZER K5 - Server Layout & Cloning (Page 1/2)",
                "description": "Export, import, cleanup or clone channel templates.",
                "fields": [
                    {"name": "• serverbuilder export", "value": "Export the server layout to a JSON file.\n*Usage:* `.serverbuilder export` or `/serverbuilder export`"},
                    {"name": "• serverbuilder import", "value": "Import a JSON server template.\n*Usage:* `.serverbuilder import <attach file>` or `/serverbuilder import`"},
                    {"name": "• serverbuilder cleanup", "value": "Delete empty categories and unused channels.\n*Usage:* `.serverbuilder cleanup` or `/serverbuilder cleanup`"},
                    {"name": "• serverbuilder clone <channel> [new_name]", "value": "Clone a channel.\n*Usage:* `.serverbuilder clone #channel` or `/serverbuilder clone channel:#channel`"}
                ]
            },
            # Page 2
            {
                "title": "🏗️ KAIZER K5 - Channel Creation & Audit (Page 2/2)",
                "description": "Create channels, categories, and verify server permissions.",
                "fields": [
                    {"name": "• serverbuilder createcategory <name> [position]", "value": "Create a new category.\n*Usage:* `.serverbuilder createcategory Rules` or `/serverbuilder createcategory name:Rules`"},
                    {"name": "• serverbuilder createchannel <name> <type> [category]", "value": "Create a new channel in a category.\n*Usage:* `.serverbuilder createchannel general text` or `/serverbuilder createchannel name:general channel_type:Text`"},
                    {"name": "• serverbuilder audit", "value": "Check for missing or broken permission overrides.\n*Usage:* `.serverbuilder audit` or `/serverbuilder audit`"}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x3498DB
        )
        for f in page_data["fields"]:
            embed.add_field(name=f["name"], value=f["value"], inline=False)
        embed.set_footer(text="KAIZER K5 • Use the buttons below to navigate pages")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the person who ran the command can use these buttons.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = len(self.pages) - 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

class ServerBuilderCog(commands.Cog, name="Server Builder"):
    """Server builder and decoration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="builder", description="Show server builder configuration help.")
    async def builder_command(self, ctx: commands.Context):
        view = BuilderHelpView(ctx.author.id)
        msg = await ctx.send(embed=view.make_embed(), view=view)
        view.message = msg

    @commands.hybrid_group(name="serverbuilder", description="Server building and management.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def serverbuilder(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = BuilderHelpView(ctx.author.id)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg

    @serverbuilder.command(name="export", description="Export the server layout to a JSON file.")
    async def server_export(self, ctx: commands.Context):
        guild = ctx.guild
        data = {
            "name": guild.name,
            "roles": [{"name": r.name, "color": str(r.color)} for r in guild.roles if not r.is_default() and not r.managed],
            "categories": []
        }
        
        for cat in guild.categories:
            c_data = {
                "name": cat.name,
                "channels": [{"name": c.name, "type": str(c.type)} for c in cat.channels]
            }
            data["categories"].append(c_data)
            
        json_bytes = json.dumps(data, indent=4).encode('utf-8')
        file = discord.File(io.BytesIO(json_bytes), filename=f"{guild.name}_template.json")
        await ctx.send(embed=discord.Embed(description="Server exported successfully.", color=discord.Color.green()), file=file)

    @serverbuilder.command(name="import", description="Import a JSON server template.")
    async def server_import(self, ctx: commands.Context, file: discord.Attachment):
        if not file.filename.endswith(".json"):
            return await ctx.send("Must be a `.json` file.")
            
        content = await file.read()
        try:
            data = json.loads(content)
        except Exception:
            return await ctx.send("Invalid JSON file.")
            
        await ctx.send("Importing template... This might take a while.")
        
        # In a real bot, we'd delete existing channels first (or have a nuke command)
        for cat_data in data.get("categories", []):
            cat = await ctx.guild.create_category(cat_data["name"])
            for chan in cat_data.get("channels", []):
                if chan["type"] == "text":
                    await cat.create_text_channel(chan["name"])
                elif chan["type"] == "voice":
                    await cat.create_voice_channel(chan["name"])
                    
        await ctx.send(embed=discord.Embed(description="Template imported successfully.", color=discord.Color.green()))

    @serverbuilder.command(name="cleanup", description="Delete empty categories and unused channels.")
    async def server_cleanup(self, ctx: commands.Context):
        count = 0
        for cat in ctx.guild.categories:
            if len(cat.channels) == 0:
                await cat.delete()
                count += 1
                
        await ctx.send(embed=discord.Embed(description=f"Cleanup complete. Deleted {count} empty categories.", color=discord.Color.green()))

    @serverbuilder.command(name="clone", description="Clone a channel.")
    async def server_clone(self, ctx: commands.Context, channel: discord.abc.GuildChannel, new_name: str = None):
        name = new_name or f"{channel.name}-clone"
        cloned = await channel.clone(name=name)
        await ctx.send(embed=discord.Embed(description=f"Cloned channel to {cloned.mention}.", color=discord.Color.green()))

    @serverbuilder.command(name="createcategory", description="Create a new category.")
    async def server_createcategory(self, ctx: commands.Context, name: str, position: int = None):
        cat = await ctx.guild.create_category(name, position=position)
        await ctx.send(embed=discord.Embed(description=f"Category `{name}` created.", color=discord.Color.green()))

    @serverbuilder.command(name="createchannel", description="Create a new channel in a category.")
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="Text", value="text"),
        app_commands.Choice(name="Voice", value="voice"),
    ])
    async def server_createchannel(self, ctx: commands.Context, name: str, channel_type: str, category: discord.CategoryChannel = None):
        if channel_type == "text":
            chan = await ctx.guild.create_text_channel(name, category=category)
        else:
            chan = await ctx.guild.create_voice_channel(name, category=category)
            
        await ctx.send(embed=discord.Embed(description=f"Channel {chan.mention} created.", color=discord.Color.green()))

    @serverbuilder.command(name="audit", description="Check for missing or broken permission overrides.")
    async def server_audit(self, ctx: commands.Context):
        issues = 0
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                overrides = channel.overwrites_for(ctx.guild.default_role)
                if overrides.read_messages is False and len(channel.changed_roles) == 0:
                    issues += 1
                    
        desc = f"Found {issues} channels that are completely hidden to everyone with no role overrides."
        if issues == 0:
            desc = "Server permissions look healthy."
            
        await ctx.send(embed=discord.Embed(title="Server Audit", description=desc, color=0x3498DB))


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerBuilderCog(bot))
