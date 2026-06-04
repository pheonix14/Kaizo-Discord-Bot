import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import time
import asyncio
import discord
from src.bot.cogs.k4_defence import K4DefenceCog

class MockGuild(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 123456789
        self.owner_id = 999999999
        self.get_channel = MagicMock(return_value=MockChannel(222, "mod-log"))

class MockRole(MagicMock):
    def __init__(self, role_id=1, name="role", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = role_id
        self.name = name

class MockChannel(MagicMock):
    def __init__(self, channel_id=222, name="channel", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = channel_id
        self.name = name
        self.send = AsyncMock()

class MockMember(MagicMock):
    def __init__(self, user_id=111, name="member", is_bot=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = user_id
        self.name = name
        self.bot = is_bot
        self.mention = f"<@{user_id}>"
        self.add_roles = AsyncMock()
        self.kick = AsyncMock()
        self.ban = AsyncMock()
        self.guild_permissions = MagicMock()
        self.guild_permissions.administrator = False
        self.guild_permissions.manage_guild = False

class MockMessage(MagicMock):
    def __init__(self, author=None, channel=None, content="", attachments=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.channel = channel
        self.content = content
        self.attachments = attachments or []
        self.created_at = MagicMock()
        self.created_at.timestamp = MagicMock(return_value=time.time())
        self.delete = AsyncMock()
        self.role_mentions = []
        self.mentions = []
        self.mention_everyone = False

class TestK4DefenceSystem(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.id = 88888888
        self.cog = K4DefenceCog(self.bot)
        self.guild = MockGuild()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_normal_chatter(self, mock_log, mock_settings, mock_whitelist):
        # Normal chat: 4 messages in 5 seconds in general chat with different content
        mock_settings.return_value = {
            "k4_defence_enabled": True,
            "mute_role": "111",
            "mod_log_channel": "222"
        }
        member = MockMember(1111, "Alice")
        channel = MockChannel(333, "general")
        
        # We send 4 messages, spaced out
        now = time.time()
        for i in range(4):
            msg = MockMessage(member, channel, f"Message number {i}")
            msg.guild = self.guild
            msg.created_at.timestamp.return_value = now + i * 1.2
            with patch('time.time', return_value=now + i * 1.2):
                await self.cog.on_message(msg)
                
        # Alice should NOT be muted
        member.add_roles.assert_not_called()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_rapid_fire_spammer(self, mock_log, mock_settings, mock_whitelist):
        # Spammer: 5 messages in 3 seconds
        mock_settings.return_value = {
            "k4_defence_enabled": True,
            "mute_role": "111",
            "mod_log_channel": "222"
        }
        member = MockMember(2222, "Bob")
        channel = MockChannel(333, "general")
        
        now = time.time()
        msgs = []
        for i in range(5):
            msg = MockMessage(member, channel, f"Spam {i}")
            msg.guild = self.guild
            msg.created_at.timestamp.return_value = now + i * 0.2
            msgs.append(msg)
            
        with patch('time.time', return_value=now + 1.0):
            for msg in msgs:
                await self.cog.on_message(msg)

        # Bob should be muted via add_roles
        member.add_roles.assert_called_once()
        # Message deletion called on Bob's messages
        for msg in msgs:
            msg.delete.assert_called()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_duplicate_same_channel_flood(self, mock_log, mock_settings, mock_whitelist):
        # Duplicate same channel: 4 identical messages in 10s
        mock_settings.return_value = {
            "k4_defence_enabled": True,
            "mute_role": "111",
            "mod_log_channel": "222"
        }
        member = MockMember(3333, "Charlie")
        channel = MockChannel(333, "general")
        
        now = time.time()
        msgs = []
        for i in range(4):
            msg = MockMessage(member, channel, "Same identical spam text")
            msg.guild = self.guild
            msg.created_at.timestamp.return_value = now + i * 1.5
            msgs.append(msg)
            
        with patch('time.time', return_value=now + 5.0):
            for msg in msgs:
                await self.cog.on_message(msg)

        # Charlie should be muted via add_roles
        member.add_roles.assert_called_once()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_mass_mention_spam(self, mock_log, mock_settings, mock_whitelist):
        # Mass mentions: 5 unique mentions in a single message
        mock_settings.return_value = {
            "k4_defence_enabled": True,
            "mute_role": "111",
            "mod_log_channel": "222"
        }
        member = MockMember(4444, "Dave")
        channel = MockChannel(333, "general")
        
        msg = MockMessage(member, channel, "Hello everyone!")
        msg.guild = self.guild
        msg.mentions = [MockMember(1, "A"), MockMember(2, "B"), MockMember(3, "C"), MockMember(4, "D"), MockMember(5, "E")]
        
        await self.cog.on_message(msg)
        
        # Dave should be muted
        member.add_roles.assert_called_once()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_whitelist_immune(self, mock_log, mock_settings, mock_whitelist):
        # Whitelisted user (admin) should NOT trigger spam mute
        mock_settings.return_value = {
            "k4_defence_enabled": True,
            "mute_role": "111",
            "mod_log_channel": "222"
        }
        member = MockMember(5555, "EveAdmin")
        member.guild_permissions.administrator = True
        channel = MockChannel(333, "general")
        
        now = time.time()
        for i in range(10):
            msg = MockMessage(member, channel, "Spam text")
            msg.guild = self.guild
            msg.created_at.timestamp.return_value = now + i * 0.1
            with patch('time.time', return_value=now + i * 0.1):
                await self.cog.on_message(msg)
                
        # EveAdmin is whitelisted, so add_roles should NOT be called
        member.add_roles.assert_not_called()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_custom_automod_newlines(self, mock_log, mock_settings, mock_whitelist):
        # Test Custom AutoMod spam_newlines rule
        mock_settings.return_value = {
            "automod_rules": {
                "rule_1": {
                    "trigger": "spam_newlines",
                    "count": 30,
                    "seconds": 10,
                    "action": "warn"
                }
            }
        }
        member = MockMember(6666, "Frank")
        channel = MockChannel(333, "general")
        
        # Create wall of text with 30 newlines
        wall_of_text = "\n" * 31
        msg = MockMessage(member, channel, wall_of_text)
        msg.guild = self.guild
        
        await self.cog.on_message(msg)
        
        # Action is warn, so warning embed should be sent
        channel.send.assert_called_once()

    @patch('src.db.client.get_guild_whitelist', return_value=[])
    @patch('src.db.client.get_guild_settings')
    @patch('src.db.client.log_protection_event')
    async def test_custom_automod_force_mute(self, mock_log, mock_settings, mock_whitelist):
        # Test custom AutoMod kick action downgrade to mute
        mock_settings.return_value = {
            "mute_role": "777",
            "automod_rules": {
                "rule_1": {
                    "trigger": "spam_messages",
                    "count": 3,
                    "seconds": 5,
                    "action": "kick" # Should downgrade to mute
                }
            }
        }
        member = MockMember(7777, "Grace")
        channel = MockChannel(333, "general")
        
        now = time.time()
        msgs = []
        for i in range(3):
            msg = MockMessage(member, channel, "normal message")
            msg.guild = self.guild
            msg.created_at.timestamp.return_value = now + i * 0.5
            msgs.append(msg)
            
        with patch('time.time', return_value=now + 1.5):
            for msg in msgs:
                await self.cog.on_message(msg)
                
        # Grace should NOT be kicked (kick forbidden or not called)
        member.kick.assert_not_called()
        # Grace should be muted instead
        member.add_roles.assert_called_once()

if __name__ == "__main__":
    unittest.main()
