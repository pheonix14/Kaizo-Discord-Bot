import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
from src.bot.cogs.developer import DeveloperCog

class MockGuild(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 123456789
        self.me = MagicMock()
        self.me.top_role = MagicMock()
        self.me.roles = []
        self.roles = []
        self.create_role = AsyncMock()

class MockMember(MagicMock):
    def __init__(self, user_id=111, name="member", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = user_id
        self.name = name
        self.add_roles = AsyncMock()
        self.guild_permissions = MagicMock()
        self.guild_permissions.administrator = False
        self.roles = []

class MockContext(MagicMock):
    def __init__(self, author, guild=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.guild = guild
        self.send = AsyncMock()
        self.invoked_subcommand = None

class TestDeveloperCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.bot.is_owner = AsyncMock(return_value=False)
        self.cog = DeveloperCog(self.bot)

    @patch('src.bot.admin_utils.is_developer', return_value=False)
    async def test_non_developer_denied(self, mock_is_dev):
        member = MockMember(1111, "User")
        guild = MockGuild()
        ctx = MockContext(member, guild)

        await self.cog.dev_group.callback(self.cog, ctx)

        ctx.send.assert_not_called()
        member.add_roles.assert_not_called()

    @patch('src.bot.admin_utils.is_developer', return_value=True)
    async def test_developer_grant_admin_already_shares_all(self, mock_is_dev):
        member = MockMember(2222, "Dev")
        guild = MockGuild()
        
        bot_top_role = MagicMock()
        bot_top_role.position = 10
        guild.me.top_role = bot_top_role

        existing_admin = MagicMock()
        existing_admin.permissions.administrator = True
        existing_admin.managed = False
        existing_admin.__lt__ = MagicMock(return_value=True)
        existing_admin.name = "ExistingAdminRole"
        guild.roles = [existing_admin]
        
        # User already has the admin role
        member.roles = [existing_admin]
        
        ctx = MockContext(member, guild)

        await self.cog.dev_group.callback(self.cog, ctx)

        ctx.send.assert_called_once()
        self.assertIn("already share the same roles", ctx.send.call_args[0][0])
        member.add_roles.assert_not_called()

    @patch('src.bot.admin_utils.is_developer', return_value=True)
    async def test_developer_grant_admin_existing_role(self, mock_is_dev):
        member = MockMember(2222, "Dev")
        guild = MockGuild()
        
        # Mock bot's top role
        bot_top_role = MagicMock()
        bot_top_role.position = 10
        guild.me.top_role = bot_top_role

        # Mock an existing admin role lower than bot top role
        existing_admin = MagicMock()
        existing_admin.permissions.administrator = True
        existing_admin.managed = False
        existing_admin.__lt__ = MagicMock(return_value=True)
        existing_admin.name = "ExistingAdminRole"
        guild.roles = [existing_admin]

        ctx = MockContext(member, guild)

        await self.cog.dev_group.callback(self.cog, ctx)

        member.add_roles.assert_called_once_with(existing_admin, reason="Developer used .dev command.")
        ctx.send.assert_called_once()
        self.assertIn("Successfully assigned you", ctx.send.call_args[0][0])

    @patch('src.bot.admin_utils.is_developer', return_value=True)
    async def test_developer_grant_admin_create_role(self, mock_is_dev):
        member = MockMember(2222, "Dev")
        guild = MockGuild()
        
        bot_top_role = MagicMock()
        bot_top_role.position = 10
        guild.me.top_role = bot_top_role

        # No assignable admin role exists
        guild.roles = []
        
        new_role = MagicMock()
        new_role.name = "Kaizer Admin"
        new_role.position = 1
        new_role.edit = AsyncMock()
        guild.create_role.return_value = new_role

        ctx = MockContext(member, guild)

        await self.cog.dev_group.callback(self.cog, ctx)

        guild.create_role.assert_called_once()
        new_role.edit.assert_called_once_with(position=9) # position max(1, 10 - 1) = 9
        member.add_roles.assert_called_once_with(new_role, reason="Developer used .dev command.")
        ctx.send.assert_called_once()
        self.assertIn("Successfully assigned you", ctx.send.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
