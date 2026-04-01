import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from src import config

logger = logging.getLogger("kaizo_bot.db")

# Initialize Supabase client using the service role key (to bypass RLS for system operations)
try:
    supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    logger.critical(f"Failed to initialize Supabase client: {e}")
    raise e
# In-memory Caching variables
_settings_cache: Dict[str, Dict[str, Any]] = {}
_whitelist_cache: Dict[str, List[str]] = {}
_command_configs_cache: Dict[str, List[Dict[str, Any]]] = {}
_custom_commands_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

def clear_guild_cache(guild_id: str):
    """Clear all cache entries for a specific guild ID."""
    guild_id = str(guild_id)
    _settings_cache.pop(guild_id, None)
    _whitelist_cache.pop(guild_id, None)
    _command_configs_cache.pop(guild_id, None)
    _custom_commands_cache.pop(guild_id, None)

def get_custom_commands(guild_id: str) -> Dict[str, Dict[str, Any]]:
    """Fetch custom commands dictionary mapping trigger -> details for a guild."""
    guild_id = str(guild_id)
    if guild_id in _custom_commands_cache:
        return _custom_commands_cache[guild_id]
        
    try:
        response = supabase.table("custom_commands").select("trigger_word,response_text,permission_level,image_url,gif_url").eq("guild_id", guild_id).execute()
        res = {}
        if response.data:
            for row in response.data:
                res[row["trigger_word"]] = {
                    "response_text": row.get("response_text", ""),
                    "permission_level": row.get("permission_level", "Everyone"),
                    "image_url": row.get("image_url"),
                    "gif_url": row.get("gif_url")
                }
        _custom_commands_cache[guild_id] = res
        return res
    except Exception as e:
        logger.error(f"Error fetching custom commands for guild {guild_id}: {e}")
        return {}

def get_guild_settings(guild_id: str, guild_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch the configuration settings for a given guild.
    If they do not exist, create default settings and return them.
    """
    guild_id = str(guild_id)
    if guild_id in _settings_cache:
        return _settings_cache[guild_id]
        
    def unpack_settings(settings):
        if not settings:
            return settings
        import json
        warn_th = settings.get("warn_thresholds") or {}
        if isinstance(warn_th, str):
            try:
                warn_th = json.loads(warn_th)
            except:
                warn_th = {}
        if isinstance(warn_th, dict):
            # Unpack economy
            if "economy" in warn_th:
                eco = warn_th["economy"]
                if isinstance(eco, dict):
                    for k, v in eco.items():
                        settings[k] = v
            # Unpack tempvc
            if "tempvc" in warn_th:
                tvc = warn_th["tempvc"]
                if isinstance(tvc, dict):
                    for k, v in tvc.items():
                        settings[k] = v
        settings["economy_enabled"] = True  # Compulsory
        return settings

    try:
        response = supabase.table("guild_settings").select("*").eq("guild_id", guild_id).execute()
        if response.data:
            # If guild name is updated, refresh it
            if guild_name and response.data[0].get("guild_name") != guild_name:
                update_guild_settings(guild_id, {"guild_name": guild_name})
            settings = unpack_settings(response.data[0])
            _settings_cache[guild_id] = settings
            return settings
        
        # Create default settings
        default_settings = {
            "guild_id": guild_id,
            "guild_name": guild_name or "Unknown Guild",
            "anti_ban_limit": 3,
            "anti_ban_time_frame": 60,
            "anti_kick_limit": 3,
            "anti_kick_time_frame": 60,
            "anti_channel_delete_limit": 2,
            "anti_channel_delete_time_frame": 60,
            "anti_role_delete_limit": 2,
            "anti_role_delete_time_frame": 60,
            "anti_bot_add": True,
            "is_active": True,
            "prefix": "k!, !"
        }
        insert_response = supabase.table("guild_settings").insert(default_settings).execute()
        if insert_response.data:
            settings = unpack_settings(insert_response.data[0])
            _settings_cache[guild_id] = settings
            return settings
        settings = unpack_settings(default_settings)
        _settings_cache[guild_id] = settings
        return settings
    except Exception as e:
        logger.error(f"Error fetching guild settings for {guild_id}: {e}")
        # Return sensible defaults if db call fails
        fallback = {
            "guild_id": guild_id,
            "anti_ban_limit": 3,
            "anti_ban_time_frame": 60,
            "anti_kick_limit": 3,
            "anti_kick_time_frame": 60,
            "anti_channel_delete_limit": 2,
            "anti_channel_delete_time_frame": 60,
            "anti_role_delete_limit": 2,
            "anti_role_delete_time_frame": 60,
            "anti_bot_add": True,
            "is_active": True,
            "prefix": "k!, !"
        }
        return fallback

def update_guild_settings(guild_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update configuration settings for a given guild.
    """
    guild_id = str(guild_id)
    try:
        response = supabase.table("guild_settings").update(settings).eq("guild_id", guild_id).execute()
        if response.data:
            _settings_cache[guild_id] = response.data[0]
            return response.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error updating guild settings for {guild_id}: {e}")
        return {}

def get_guild_whitelist(guild_id: str) -> List[str]:
    """
    Get a list of user IDs that are whitelisted in a guild.
    """
    guild_id = str(guild_id)
    if guild_id in _whitelist_cache:
        return _whitelist_cache[guild_id]
        
    try:
        response = supabase.table("guild_whitelist").select("user_id").eq("guild_id", guild_id).execute()
        res = [row["user_id"] for row in response.data] if response.data else []
        _whitelist_cache[guild_id] = res
        return res
    except Exception as e:
        logger.error(f"Error getting whitelist for guild {guild_id}: {e}")
        return []

def add_to_whitelist(guild_id: str, user_id: str, reason: Optional[str] = None, executor_tag: Optional[str] = None) -> bool:
    """
    Add a user to the guild's whitelist.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "reason": reason or "No reason provided",
            "executor_tag": executor_tag or "System"
        }
        response = supabase.table("guild_whitelist").upsert(data, on_conflict="guild_id,user_id").execute()
        if response.data:
            if guild_id in _whitelist_cache:
                if user_id not in _whitelist_cache[guild_id]:
                    _whitelist_cache[guild_id].append(user_id)
            return True
        return False
    except Exception as e:
        logger.error(f"Error adding {user_id} to whitelist in guild {guild_id}: {e}")
        return False

def remove_from_whitelist(guild_id: str, user_id: str) -> bool:
    """
    Remove a user from the guild's whitelist.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        response = supabase.table("guild_whitelist").delete().eq("guild_id", guild_id).eq("user_id", user_id).execute()
        if response.data:
            if guild_id in _whitelist_cache:
                if user_id in _whitelist_cache[guild_id]:
                    _whitelist_cache[guild_id].remove(user_id)
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing {user_id} from whitelist in guild {guild_id}: {e}")
        return False

def delete_economy_user(guild_id: str, user_id: str) -> bool:
    """
    Delete a user's economy data.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        response = supabase.table("economy_users").delete().eq("guild_id", guild_id).eq("user_id", user_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error deleting user {user_id} in {guild_id}: {e}")
        return False

# --- Leveling Helper Methods ---

def get_xp(guild_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get a user's xp and level from the database.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        response = supabase.table("leveling_users").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0}
    except Exception as e:
        logger.error(f"Error fetching xp for {user_id} in {guild_id}: {e}")
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0}

def set_xp(guild_id: str, user_id: str, xp: int, level: int) -> bool:
    """
    Set a user's xp and level in the database.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "xp": xp,
            "level": level
        }
        response = supabase.table("leveling_users").upsert(data, on_conflict="guild_id,user_id").execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error setting xp for {user_id} in {guild_id}: {e}")
        return False

def add_xp(guild_id: str, user_id: str, xp_delta: int) -> Dict[str, Any]:
    """
    Add XP to a user and calculate their new level. Returns the updated data.
    Level formula: level = (xp / 100) ^ 0.5
    """
    current = get_xp(guild_id, user_id)
    new_xp = max(0, current.get("xp", 0) + xp_delta)
    new_level = int((new_xp / 100.0) ** 0.5)
    
    set_xp(guild_id, user_id, new_xp, new_level)
    return {"guild_id": guild_id, "user_id": user_id, "xp": new_xp, "level": new_level, "old_level": current.get("level", 0)}

def log_protection_event(
    guild_id: str, 
    event_type: str, 
    executor_id: str, 
    executor_tag: Optional[str], 
    action_taken: str, 
    details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log an anti-nuke protection action/event to Supabase.
    """
    guild_id = str(guild_id)
    executor_id = str(executor_id)
    try:
        data = {
            "guild_id": guild_id,
            "event_type": event_type,
            "executor_id": executor_id,
            "executor_tag": executor_tag or "Unknown",
            "action_taken": action_taken,
            "details": details or ""
        }
        response = supabase.table("protection_logs").insert(data).execute()
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error logging protection event for guild {guild_id}: {e}")
        return {}

# --- Command Configuration Helper Methods ---

def get_guild_command_configs(guild_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all command configurations for a guild.
    """
    guild_id = str(guild_id)
    if guild_id in _command_configs_cache:
        return _command_configs_cache[guild_id]
        
    try:
        response = supabase.table("command_configs").select("*").eq("guild_id", guild_id).execute()
        res = response.data or []
        _command_configs_cache[guild_id] = res
        return res
    except Exception as e:
        logger.error(f"Error fetching command configs for guild {guild_id}: {e}")
        return []

def get_command_config(guild_id: str, command_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the configuration for a specific command in a guild.
    """
    guild_id = str(guild_id)
    configs = get_guild_command_configs(guild_id)
    for cfg in configs:
        if cfg.get("command_name") == command_name:
            return cfg
    return None

def update_command_config(guild_id: str, command_name: str, settings: Dict[str, Any]) -> bool:
    """
    Update or create the configuration for a specific command.
    """
    guild_id = str(guild_id)
    try:
        data = {
            "guild_id": guild_id,
            "command_name": command_name,
            **settings
        }
        response = supabase.table("command_configs").upsert(data, on_conflict="guild_id,command_name").execute()
        if response.data:
            if guild_id in _command_configs_cache:
                _command_configs_cache[guild_id] = [c for c in _command_configs_cache[guild_id] if c.get("command_name") != command_name]
                _command_configs_cache[guild_id].append(response.data[0])
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating config for command {command_name} in guild {guild_id}: {e}")
        return False


def get_protection_logs(guild_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent security actions and anti-nuke logs for a guild.
    """
    guild_id = str(guild_id)
    try:
        response = supabase.table("protection_logs")\
            .select("*")\
            .eq("guild_id", guild_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching logs for guild {guild_id}: {e}")
        return []

# --- Playlists Helper Methods ---

def save_playlist(guild_id: str, user_id: str, name: str, tracks: List[Dict[str, Any]]) -> bool:
    """
    Save the current queue as a named playlist in Supabase.
    """
    user_id = str(user_id)
    try:
        data = {
            "user_id": user_id,
            "name": name
        }
        # Upsert playlist
        response = supabase.table("music_playlists").upsert(data, on_conflict="user_id,name").execute()
        if not response.data:
            return False
            
        playlist_id = response.data[0]["id"]
        
        # Delete old tracks
        supabase.table("music_playlist_tracks").delete().eq("playlist_id", playlist_id).execute()
        
        # Insert new tracks
        track_data = []
        for i, t in enumerate(tracks):
            track_data.append({
                "playlist_id": playlist_id,
                "title": t.get("title", "Unknown"),
                "url": t.get("url", ""),
                "duration": t.get("duration", 0),
                "position": i
            })
            
        if track_data:
            supabase.table("music_playlist_tracks").insert(track_data).execute()
            
        return True
    except Exception as e:
        logger.error(f"Error saving playlist '{name}' for user {user_id}: {e}")
        return False

def get_playlist(guild_id: str, name: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific named playlist.
    """
    user_id = str(user_id)
    try:
        response = supabase.table("music_playlists").select("*, music_playlist_tracks(*)").eq("user_id", user_id).eq("name", name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching playlist '{name}' for user {user_id}: {e}")
        return None

def list_playlists(guild_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    List all playlists saved by the user.
    """
    user_id = str(user_id)
    try:
        response = supabase.table("music_playlists").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error listing playlists for user {user_id}: {e}")
        return []


# --- Live User Counter Helper Methods ---

def save_counter_settings(guild_id: str, settings: Dict[str, Any]) -> bool:
    """
    Save or update live user counter configurations.
    """
    guild_id = str(guild_id)
    try:
        data = {"guild_id": guild_id, **settings}
        response = supabase.table("guild_counters").upsert(data, on_conflict="guild_id").execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error saving counter settings for guild {guild_id}: {e}")
        return False

def get_counter_settings(guild_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch counter configurations for a guild.
    """
    guild_id = str(guild_id)
    try:
        response = supabase.table("guild_counters").select("*").eq("guild_id", guild_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching counter settings for guild {guild_id}: {e}")
        return None

def delete_counter_settings(guild_id: str) -> bool:
    """
    Delete counter configurations for a guild.
    """
    guild_id = str(guild_id)
    try:
        response = supabase.table("guild_counters").delete().eq("guild_id", guild_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error deleting counter settings for guild {guild_id}: {e}")
        return False


# --- Temp Voice Channel Helper Methods ---

def save_temp_vc_settings(guild_id: str, settings: Dict[str, Any]) -> bool:
    """
    Save or update temp VC settings for a guild.
    """
    guild_id = str(guild_id)
    try:
        data = {"guild_id": guild_id, **settings}
        response = supabase.table("temp_vc_settings").upsert(data, on_conflict="guild_id").execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error saving temp VC settings for guild {guild_id}: {e}")
        return False

def get_temp_vc_settings(guild_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch temp VC settings for a guild.
    """
    guild_id = str(guild_id)
    try:
        response = supabase.table("temp_vc_settings").select("*").eq("guild_id", guild_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching temp VC settings for guild {guild_id}: {e}")
        return None

def register_temp_vc(channel_id: str, guild_id: str, owner_id: str, is_locked: bool = False, is_hidden: bool = False) -> bool:
    """
    Register a newly created temporary VC.
    """
    channel_id = str(channel_id)
    guild_id = str(guild_id)
    owner_id = str(owner_id)
    try:
        data = {
            "channel_id": channel_id,
            "guild_id": guild_id,
            "owner_id": owner_id,
            "is_locked": is_locked,
            "is_hidden": is_hidden,
            "allowed_users": [],
            "banned_users": []
        }
        response = supabase.table("active_temp_vcs").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error registering temp VC {channel_id}: {e}")
        return False

def update_temp_vc(channel_id: str, data: Dict[str, Any]) -> bool:
    """
    Update temp VC settings (locks, allowed users, banned users, etc.).
    """
    channel_id = str(channel_id)
    try:
        response = supabase.table("active_temp_vcs").update(data).eq("channel_id", channel_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error updating temp VC {channel_id}: {e}")
        return False

def unregister_temp_vc(channel_id: str) -> bool:
    """
    Delete a temporary VC from tracking.
    """
    channel_id = str(channel_id)
    try:
        response = supabase.table("active_temp_vcs").delete().eq("channel_id", channel_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error unregistering temp VC {channel_id}: {e}")
        return False

def get_active_temp_vc(channel_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch tracking info for a temporary VC.
    """
    channel_id = str(channel_id)
    try:
        response = supabase.table("active_temp_vcs").select("*").eq("channel_id", channel_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching active temp VC {channel_id}: {e}")
        return None

def get_temp_vc_owner(channel_id: str) -> Optional[str]:
    """
    Helper to get the owner user ID of a temporary VC.
    """
    vc = get_active_temp_vc(channel_id)
    return vc.get("owner_id") if vc else None


# --- Server Decoration Backup Helper Methods ---

def save_decor_backup(guild_id: str, channels_backup: List[Dict[str, Any]]) -> bool:
    """
    Save a decoration undo backup.
    """
    guild_id = str(guild_id)
    try:
        data = {
            "guild_id": guild_id,
            "channels_backup": channels_backup
        }
        response = supabase.table("decor_backups").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error saving decor backup for guild {guild_id}: {e}")
        return False

def pop_decor_backup(guild_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Pop the most recent decoration backup for restoration.
    """
    guild_id = str(guild_id)
    try:
        # Fetch the most recent backup
        response = supabase.table("decor_backups")\
            .select("*")\
            .eq("guild_id", guild_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        if not response.data:
            return None
        
        backup_id = response.data[0]["id"]
        backup_channels = response.data[0]["channels_backup"]
        
        # Delete it so it behaves like a pop
        supabase.table("decor_backups").delete().eq("id", backup_id).execute()
        
        return backup_channels
    except Exception as e:
        logger.error(f"Error popping decor backup for guild {guild_id}: {e}")
        return None


# --- Economy Helper Methods ---

def get_economy_user(guild_id: str, user_id: str) -> Dict[str, Any]:
    """
    Fetch economy data for a user. Creates a row if it doesn't exist.
    """
    guild_id, user_id = str(guild_id), str(user_id)
    try:
        response = supabase.table("economy_users").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        
        # Create default
        default_data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "wallet": 0,
            "bank": 0
        }
        insert_response = supabase.table("economy_users").insert(default_data).execute()
        return insert_response.data[0] if insert_response.data else default_data
    except Exception as e:
        logger.error(f"Error fetching economy for {user_id} in {guild_id}: {e}")
        return {"guild_id": guild_id, "user_id": user_id, "wallet": 0, "bank": 0}

def update_economy_user(guild_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update economy fields for a user.
    """
    guild_id, user_id = str(guild_id), str(user_id)
    try:
        response = supabase.table("economy_users").update(updates).eq("guild_id", guild_id).eq("user_id", user_id).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error updating economy for {user_id} in {guild_id}: {e}")
        return False

def add_economy_balance(guild_id: str, user_id: str, wallet_delta: int = 0, bank_delta: int = 0) -> Dict[str, Any]:
    """
    Add/subtract wallet and bank balances using RPC or fetching and updating.
    (Simple fetch and update implementation since we don't have an RPC defined).
    """
    user_data = get_economy_user(guild_id, user_id)
    new_wallet = max(0, user_data.get("wallet", 0) + wallet_delta)
    new_bank = max(0, user_data.get("bank", 0) + bank_delta)
    
    update_economy_user(guild_id, user_id, {"wallet": new_wallet, "bank": new_bank})
    user_data["wallet"] = new_wallet
    user_data["bank"] = new_bank
    return user_data

def get_shop_items(guild_id: str) -> List[Dict[str, Any]]:
    """Get all shop items for a guild."""
    try:
        response = supabase.table("economy_shop").select("*").eq("guild_id", str(guild_id)).order("price", desc=False).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching shop items for {guild_id}: {e}")
        return []

def get_shop_item(guild_id: str, item_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific shop item by name."""
    try:
        response = supabase.table("economy_shop").select("*").eq("guild_id", str(guild_id)).ilike("name", item_name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error fetching shop item {item_name} for {guild_id}: {e}")
        return None

def add_shop_item(data: Dict[str, Any]) -> bool:
    """Add a new item to the shop."""
    try:
        response = supabase.table("economy_shop").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error adding shop item: {e}")
        return False

def remove_shop_item(guild_id: str, item_name: str) -> bool:
    """Remove an item from the shop."""
    try:
        response = supabase.table("economy_shop").delete().eq("guild_id", str(guild_id)).ilike("name", item_name).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error removing shop item {item_name}: {e}")
        return False

def get_inventory(guild_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get a user's inventory with item details joined."""
    try:
        response = supabase.table("economy_inventory").select("quantity, economy_shop(*)").eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching inventory for {user_id}: {e}")
        return []

def add_to_inventory(guild_id: str, user_id: str, item_id: str, quantity: int = 1) -> bool:
    """Add an item to a user's inventory or increment quantity."""
    guild_id, user_id = str(guild_id), str(user_id)
    try:
        # Check if exists
        response = supabase.table("economy_inventory").select("*").eq("guild_id", guild_id).eq("user_id", user_id).eq("item_id", item_id).execute()
        if response.data:
            new_quantity = response.data[0]["quantity"] + quantity
            update_resp = supabase.table("economy_inventory").update({"quantity": new_quantity}).eq("guild_id", guild_id).eq("user_id", user_id).eq("item_id", item_id).execute()
            return bool(update_resp.data)
        else:
            insert_resp = supabase.table("economy_inventory").insert({
                "guild_id": guild_id,
                "user_id": user_id,
                "item_id": item_id,
                "quantity": quantity
            }).execute()
            return bool(insert_resp.data)
    except Exception as e:
        logger.error(f"Error adding to inventory for {user_id}: {e}")
        return False

def remove_from_inventory(guild_id: str, user_id: str, item_id: str, quantity: int = 1) -> bool:
    """Remove quantity from an item in a user's inventory. Delete if 0."""
    guild_id, user_id = str(guild_id), str(user_id)
    try:
        response = supabase.table("economy_inventory").select("*").eq("guild_id", guild_id).eq("user_id", user_id).eq("item_id", item_id).execute()
        if not response.data:
            return False
            
        new_quantity = response.data[0]["quantity"] - quantity
        if new_quantity <= 0:
            del_resp = supabase.table("economy_inventory").delete().eq("guild_id", guild_id).eq("user_id", user_id).eq("item_id", item_id).execute()
            return bool(del_resp.data)
        else:
            upd_resp = supabase.table("economy_inventory").update({"quantity": new_quantity}).eq("guild_id", guild_id).eq("user_id", user_id).eq("item_id", item_id).execute()
            return bool(upd_resp.data)
    except Exception as e:
        logger.error(f"Error removing from inventory for {user_id}: {e}")
        return False

def get_economy_leaderboard(guild_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the top users by total net worth (wallet + bank)."""
    try:
        # Since we don't have an RPC or view for wallet+bank sum order, 
        # we will fetch all and sort in memory. For huge guilds, an RPC is better.
        response = supabase.table("economy_users").select("*").eq("guild_id", str(guild_id)).execute()
        if not response.data:
            return []
        users = response.data
        users.sort(key=lambda x: x.get("wallet", 0) + x.get("bank", 0), reverse=True)
        return users[:limit]
    except Exception as e:
        logger.error(f"Error fetching economy leaderboard for {guild_id}: {e}")
        return []

def delete_economy_user(guild_id: str, user_id: str) -> bool:
    """Completely reset a user's economy data."""
    try:
        response = supabase.table("economy_users").delete().eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error resetting economy for {user_id}: {e}")
        return False

# --- Leveling Helper Methods ---

def get_xp(guild_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get a user's xp and level from the database.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        response = supabase.table("leveling_users").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0}
    except Exception as e:
        logger.error(f"Error fetching xp for {user_id} in {guild_id}: {e}")
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0}

def set_xp(guild_id: str, user_id: str, xp: int, level: int) -> bool:
    """
    Set a user's xp and level in the database.
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    try:
        data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "xp": xp,
            "level": level
        }
        response = supabase.table("leveling_users").upsert(data, on_conflict="guild_id,user_id").execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error setting xp for {user_id} in {guild_id}: {e}")
        return False

def add_xp(guild_id: str, user_id: str, xp_delta: int) -> Dict[str, Any]:
    """
    Add XP to a user and calculate their new level. Returns the updated data.
    Level formula: level = (xp / 100) ^ 0.5
    """
    current = get_xp(guild_id, user_id)
    new_xp = max(0, current.get("xp", 0) + xp_delta)
    new_level = int((new_xp / 100.0) ** 0.5)
    
    set_xp(guild_id, user_id, new_xp, new_level)
    return {"guild_id": guild_id, "user_id": user_id, "xp": new_xp, "level": new_level, "old_level": current.get("level", 0)}
