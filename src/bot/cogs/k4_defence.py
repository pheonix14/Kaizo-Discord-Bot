import discord
from discord.ext import commands
from discord import app_commands
import time
import hashlib
import asyncio
import re
from typing import Dict, List, Tuple
from src.db import client as db_client

URL_REGEX = re.compile(r"https?://[^\s]+")
INVITE_REGEX = re.compile(r"(discord\.gg/|discord\.com/invite/)[^\s]+")

class K4DefenceCog(commands.Cog, name="K4 Defence"):
    """Advanced anti-spam and anti-raid protection system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id -> list of message records: (channel_id, timestamp, content_hash)
        self.message_cache: Dict[str, List[Tuple[str, float, str]]] = {}
        # user_id -> list of message IDs for rapid deletion
        self.message_objects: Dict[str, List[discord.Message]] = {}
        
        # custom AutoMod rate caches
        # guild_id -> user_id -> list of records: {"timestamp": float, "attachments": int, "mentions": int, "channel_id": str}
        self.spam_cache: Dict[str, Dict[str, List[dict]]] = {}
        # user_id -> list of message objects for deletion
        self.custom_message_objects: Dict[str, List[discord.Message]] = {}
        
        # user_id -> timestamp when muted (grace period to avoid double trigger)
        self.mute_grace_cache: Dict[str, float] = {}

    def get_content_hash(self, message: discord.Message) -> str:
        """Create a hash representing the message content and attachments."""
        content = message.content or ""
        attachments = "".join([a.url for a in message.attachments])
        return hashlib.md5((content + attachments).encode('utf-8')).hexdigest()

    async def punish_user(self, member: discord.Member, guild: discord.Guild, reason: str):
        """Mutes the user permanently and logs to modlog."""
        # Register in mute grace cache to avoid duplicate actions
        self.mute_grace_cache[str(member.id)] = time.time()

        settings = await asyncio.to_thread(db_client.get_guild_settings, str(guild.id))
        mute_role_id = settings.get("mute_role")
        
        # 1. Assign Mute Role
        if mute_role_id:
            role = guild.get_role(int(mute_role_id))
            if role:
                try:
                    await member.add_roles(role, reason=f"K4 Defence triggered: {reason}")
                except discord.Forbidden:
                    pass
        
        # 2. Log to Mod Log
        modlog_id = settings.get("mod_log_channel")
        if modlog_id:
            modlog = guild.get_channel(int(modlog_id))
            if modlog:
                embed = discord.Embed(
                    title="[K4 Defence] Triggered",
                    description=f"**User:** {member.mention} ({member.id})\n**Action:** Muted\n**Reason:** {reason}\n*User must open a ticket to appeal.*",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                try:
                    await modlog.send(embed=embed)
                except discord.Forbidden:
                    pass
                    
        # 3. Log to DB Protection Logs
        await asyncio.to_thread(db_client.log_protection_event, str(guild.id), "k4_defence", str(self.bot.user.id), "System", "Muted", f"Target: {member.id}. Reason: {reason}")

    async def execute_automod_action(self, member: discord.Member, guild: discord.Guild, channel: discord.TextChannel, action: str, reason: str, user_id: str):
        """Execute action for custom AutoMod rule trigger."""
        # Force mute-only: downgrade ban/kick actions
        if action in ["ban", "kick"]:
            action = "mute"
            reason = f"{reason} (Downgraded to mute)"

        settings = await asyncio.to_thread(db_client.get_guild_settings, str(guild.id))
        mute_role_id = settings.get("mute_role")
        modlog_id = settings.get("mod_log_channel")
        
        # 1. Delete matching messages from the last 60 seconds (spam messages)
        if user_id in self.custom_message_objects:
            for msg in self.custom_message_objects[user_id]:
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
        
        # 2. Perform Action
        action_name = "None"
        if action == "mute":
            action_name = "Muted permanently"
            # Register in mute grace cache to avoid duplicate actions
            self.mute_grace_cache[str(member.id)] = time.time()
            if mute_role_id:
                role = guild.get_role(int(mute_role_id))
                if role:
                    try:
                        await member.add_roles(role, reason=f"AutoMod triggered: {reason}")
                    except discord.Forbidden:
                        pass
        elif action == "warn":
            action_name = "Warned"
            # Send warning message/embed to channel
            embed = discord.Embed(
                title="[Warning]",
                description=f"{member.mention}, please stop. **Reason:** {reason}",
                color=discord.Color.orange()
            )
            try:
                await channel.send(embed=embed, delete_after=10)
            except discord.Forbidden:
                pass
        elif action == "kick":
            action_name = "Kicked"
            try:
                await member.kick(reason=f"AutoMod triggered: {reason}")
            except discord.Forbidden:
                pass
        elif action == "ban":
            action_name = "Banned"
            try:
                await member.ban(reason=f"AutoMod triggered: {reason}")
            except discord.Forbidden:
                pass
                
        # 3. Log to Mod Log channel
        if modlog_id:
            modlog = guild.get_channel(int(modlog_id))
            if modlog:
                embed = discord.Embed(
                    title="[AutoMod] Rule Triggered",
                    description=f"**User:** {member.mention} ({member.id})\n**Action Taken:** {action_name}\n**Reason:** {reason}",
                    color=discord.Color.red() if action in ["ban", "kick", "mute"] else discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                try:
                    await modlog.send(embed=embed)
                except discord.Forbidden:
                    pass
                    
        # 4. Log to DB Protection Logs
        await asyncio.to_thread(
            db_client.log_protection_event,
            str(guild.id),
            "automod",
            str(self.bot.user.id),
            "System AutoMod",
            action_name,
            f"Target: {member.id}. Reason: {reason}"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        current_time = time.time()

        # 0. Check mute grace period
        if user_id in self.mute_grace_cache:
            if current_time - self.mute_grace_cache[user_id] < 30.0:
                # Still in grace period, ignore
                return
            else:
                self.mute_grace_cache.pop(user_id, None)

        # 0.1 Check Whitelist Protection (owner, admins, mods, whitelisted users are immune)
        is_whitelisted = False
        if message.author.id == message.guild.owner_id:
            is_whitelisted = True
        elif message.author.guild_permissions.administrator:
            is_whitelisted = True
        elif message.author.guild_permissions.manage_guild:
            is_whitelisted = True
        else:
            # Check database whitelist
            try:
                whitelist_ids = await asyncio.to_thread(db_client.get_guild_whitelist, guild_id)
                if str(message.author.id) in whitelist_ids:
                    is_whitelisted = True
            except Exception:
                # Fallback in case of database errors
                pass
        
        if is_whitelisted:
            return

        settings = await asyncio.to_thread(db_client.get_guild_settings, guild_id)
        
        # 1. Evaluate custom AutoMod rules (Creator Studio)
        automod_rules = settings.get("automod_rules", {})
        if automod_rules:
            if guild_id not in self.spam_cache:
                self.spam_cache[guild_id] = {}
            if user_id not in self.spam_cache[guild_id]:
                self.spam_cache[guild_id][user_id] = []
            if user_id not in self.custom_message_objects:
                self.custom_message_objects[user_id] = []
                
            attachment_count = len(message.attachments)
            mention_count = len(message.mentions) + len(message.role_mentions) + (1 if message.mention_everyone else 0)
            
            # Extract URLs & Invites
            url_count = len(URL_REGEX.findall(message.content or ""))
            invite_count = len(INVITE_REGEX.findall(message.content or ""))
            
            # Newlines / length
            newline_count = message.content.count("\n") if message.content else 0
            char_count = len(message.content) if message.content else 0
            
            content_hash = self.get_content_hash(message)

            self.spam_cache[guild_id][user_id].append({
                "timestamp": current_time,
                "attachments": attachment_count,
                "mentions": mention_count,
                "urls": url_count,
                "invites": invite_count,
                "newlines": newline_count,
                "length": char_count,
                "hash": content_hash,
                "channel_id": str(message.channel.id)
            })
            self.custom_message_objects[user_id].append(message)
            
            # Prune cache older than 60 seconds
            self.spam_cache[guild_id][user_id] = [m for m in self.spam_cache[guild_id][user_id] if m["timestamp"] >= current_time - 60.0]
            self.custom_message_objects[user_id] = [msg for msg in self.custom_message_objects[user_id] if msg.created_at.timestamp() >= current_time - 60.0]
            
            recent_activities = self.spam_cache[guild_id][user_id]
            
            # If rules is a list or dict, normalize to iterable
            rules_list = automod_rules.values() if isinstance(automod_rules, dict) else automod_rules
            for rule in rules_list:
                if not isinstance(rule, dict):
                    continue
                trigger = rule.get("trigger")
                count = int(rule.get("count", 0))
                seconds = int(rule.get("seconds", 0))
                action = rule.get("action", "mute")
                
                if not trigger or count <= 0 or seconds <= 0:
                    continue
                
                recent_window = [m for m in recent_activities if m["timestamp"] >= current_time - seconds]
                
                triggered = False
                reason = ""
                
                if trigger == "spam_messages":
                    if len(recent_window) >= count:
                        triggered = True
                        reason = f"Spamming messages ({len(recent_window)} messages in {seconds}s)"
                elif trigger == "spam_attachments":
                    tot_attach = sum(m["attachments"] for m in recent_window)
                    if tot_attach >= count:
                        triggered = True
                        reason = f"Spamming attachments/files ({tot_attach} attachments in {seconds}s)"
                elif trigger == "spam_mentions":
                    tot_mentions = sum(m["mentions"] for m in recent_window)
                    if tot_mentions >= count:
                        triggered = True
                        reason = f"Spamming mentions/pings ({tot_mentions} mentions in {seconds}s)"
                elif trigger == "spam_links":
                    tot_urls = sum(m["urls"] for m in recent_window)
                    if tot_urls >= count:
                        triggered = True
                        reason = f"Spamming links/URLs ({tot_urls} links in {seconds}s)"
                elif trigger == "spam_invites":
                    tot_invites = sum(m["invites"] for m in recent_window)
                    if tot_invites >= count:
                        triggered = True
                        reason = f"Spamming Discord invites ({tot_invites} invites in {seconds}s)"
                elif trigger == "spam_newlines":
                    large_msg = next((m for m in recent_window if m["newlines"] >= count or m["length"] >= 4000 or m["newlines"] >= 30), None)
                    if large_msg:
                        triggered = True
                        reason = f"Wall-of-text / Newline flood ({large_msg['newlines']} newlines, {large_msg['length']} chars)"
                elif trigger == "spam_duplicates":
                    from collections import Counter
                    hash_counts = Counter((m["channel_id"], m["hash"]) for m in recent_window)
                    if hash_counts:
                        max_dup = max(hash_counts.values())
                        if max_dup >= count:
                            triggered = True
                            reason = f"Duplicate content flood ({max_dup} identical messages in {seconds}s)"
                        
                if triggered:
                    await self.execute_automod_action(message.author, message.guild, message.channel, action, reason, user_id)
                    self.spam_cache[guild_id][user_id] = []
                    self.custom_message_objects[user_id] = []
                    return

        # 2. Standard K4 Defence checks
        if not settings.get("k4_defence_enabled", False):
            return

        content_hash = self.get_content_hash(message)

        # Initialize cache for user
        if user_id not in self.message_cache:
            self.message_cache[user_id] = []
            self.message_objects[user_id] = []

        # Add current message
        self.message_cache[user_id].append((str(message.channel.id), current_time, content_hash))
        self.message_objects[user_id].append(message)

        # Clean up cache older than 15 seconds
        cutoff = current_time - 15.0
        self.message_cache[user_id] = [m for m in self.message_cache[user_id] if m[1] >= cutoff]
        self.message_objects[user_id] = [m for m in self.message_objects[user_id] if m.created_at.timestamp() >= cutoff]

        recent_messages = self.message_cache[user_id]

        triggered = False
        reason = ""

        # RULE 1: Cross-channel Exact Match Spam (3+ channels in 15 seconds)
        channels_with_hash = set(m[0] for m in recent_messages if m[2] == content_hash)
        if len(channels_with_hash) >= 3:
            triggered = True
            reason = "Sent exact same message/image in 3+ channels simultaneously."

        # RULE 2: Rapid Speed Spam (5+ messages within 3 seconds)
        fast_cutoff = current_time - 3.0
        fast_messages = [m for m in recent_messages if m[1] >= fast_cutoff]
        if len(fast_messages) >= 5:
            triggered = True
            reason = "Rapid fire spam (5+ messages in 3 seconds)."

        # NEW RULE 3: Duplicate content flood (4+ identical messages in 10s (same channel))
        if not triggered:
            dup_cutoff = current_time - 10.0
            dup_messages = [m for m in recent_messages if m[1] >= dup_cutoff and m[2] == content_hash and m[0] == str(message.channel.id)]
            if len(dup_messages) >= 4:
                triggered = True
                reason = f"Duplicate content flood (4+ identical messages in 10 seconds in same channel)."

        # NEW RULE 4: Mass mention spam (5+ unique mentions in a single message)
        if not triggered:
            unique_mentions = len(set(m.id for m in message.mentions))
            if unique_mentions >= 5:
                triggered = True
                reason = f"Mass mention spam ({unique_mentions} unique mentions in message)."

        # NEW RULE 5: Newline/wall-of-text bomb (30+ newlines or 4000+ chars)
        if not triggered:
            newline_count = message.content.count("\n") if message.content else 0
            char_count = len(message.content) if message.content else 0
            if newline_count >= 30 or char_count >= 4000:
                triggered = True
                reason = f"Wall-of-text bomb ({newline_count} newlines, {char_count} characters)."

        # NEW RULE 6: Link flood (4+ URLs in 8s)
        if not triggered:
            link_cutoff = current_time - 8.0
            recent_msgs_8s = [m for m in self.message_objects[user_id] if m.created_at.timestamp() >= link_cutoff]
            total_urls = sum(len(URL_REGEX.findall(msg.content or "")) for msg in recent_msgs_8s)
            if total_urls >= 4:
                triggered = True
                reason = f"Link flood ({total_urls} URLs in 8 seconds)."

        # NEW RULE 7: Invite link spam (2+ Discord invite links in 10s)
        if not triggered:
            invite_cutoff = current_time - 10.0
            recent_msgs_10s = [m for m in self.message_objects[user_id] if m.created_at.timestamp() >= invite_cutoff]
            total_invites = sum(len(INVITE_REGEX.findall(msg.content or "")) for msg in recent_msgs_10s)
            if total_invites >= 2:
                triggered = True
                reason = f"Discord invite spam ({total_invites} invites in 10 seconds)."

        if triggered:
            # 1. Punish User
            await self.punish_user(message.author, message.guild, reason)
            
            # 2. Delete all flagged messages
            for msg in self.message_objects[user_id]:
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass # Already deleted
                except discord.Forbidden:
                    pass
            
            # 3. Clear cache for this user so we don't double-trigger
            self.message_cache[user_id] = []
            self.message_objects[user_id] = []

    # ── Commands ─────────────────────────────────────────────────────────────

    @commands.hybrid_group(name="k4defence", description="K4 Defence anti-spam/anti-raid system.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def k4defence(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @k4defence.command(name="enable", description="Enable K4 Defence system.")
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx: commands.Context):
        # We need to gracefully handle if the DB column isn't added yet
        try:
            await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"k4_defence_enabled": True})
            await ctx.send(embed=discord.Embed(description="[OK] **K4 Defence has been ENABLED.**", color=discord.Color.green()))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description="[Warning] Database error. Ensure `k4_defence_enabled` column exists in Supabase.", color=discord.Color.red()))
 
    @k4defence.command(name="disable", description="Disable K4 Defence system.")
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx: commands.Context):
        try:
            await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"k4_defence_enabled": False})
            await ctx.send(embed=discord.Embed(description="[OFF] **K4 Defence has been DISABLED.**", color=discord.Color.red()))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description="[Warning] Database error.", color=discord.Color.red()))
 
    @k4defence.command(name="status", description="Check if K4 Defence is currently active.")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx: commands.Context):
        settings = await asyncio.to_thread(db_client.get_guild_settings, str(ctx.guild.id))
        is_enabled = settings.get("k4_defence_enabled", False)
        
        status_text = "**ENABLED**" if is_enabled else "**DISABLED**"
        embed = discord.Embed(
            title="[K4 Defence] Status",
            description=f"Current Status: {status_text}\n\n*If triggered, K4 Defence automatically deletes spam and permanently mutes the user.*",
            color=discord.Color.green() if is_enabled else discord.Color.red()
        )
        
        mute_role_id = settings.get("mute_role")
        if mute_role_id:
            embed.add_field(name="Mute Role", value=f"<@&{mute_role_id}>", inline=False)
        else:
            embed.add_field(name="[Warning] Mute Role Missing", value="No mute role configured! K4 Defence will delete messages but cannot mute users. Please set a mute role via Dashboard or `/automod modlog_set`.", inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(K4DefenceCog(bot))
