import discord
from discord.ext import commands
import json
import logging
import asyncio
import io
import math
import random
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from src.db import client as db_client

logger = logging.getLogger("kaizer_k5.welcome")

# ---------------------------------------------------------------------------
# PIL Image Card Customization Configuration
# ---------------------------------------------------------------------------
THEMES = {
    "cyan_neon": {"primary": (10, 254, 228), "secondary": (0, 85, 255)},
    "red_hot": {"primary": (239, 68, 68), "secondary": (153, 27, 27)},
    "emerald_green": {"primary": (16, 185, 129), "secondary": (6, 78, 59)},
    "golden_hour": {"primary": (251, 191, 36), "secondary": (180, 83, 9)},
    "electric_purple": {"primary": (168, 85, 247), "secondary": (76, 29, 149)},
    "synthwave_pink": {"primary": (236, 72, 153), "secondary": (80, 7, 36)},
    "dark_space": {"primary": (30, 41, 59), "secondary": (15, 23, 42)},
    "ice_blue": {"primary": (56, 189, 248), "secondary": (30, 58, 138)}
}

async def fetch_avatar(url: str) -> Image.Image:
    """Fetch avatar image from Discord CDN with robust error fallback."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data))
    except Exception as e:
        logger.error(f"Failed to fetch avatar from {url}: {e}")
    # Return grey fallback avatar if download fails
    dummy = Image.new("RGBA", (128, 128), (30, 41, 59, 255))
    draw = ImageDraw.Draw(dummy)
    draw.ellipse([10, 10, 118, 118], fill=(100, 116, 139, 255))
    return dummy

async def fetch_custom_bg(url: str) -> Image.Image:
    """Fetch user-provided custom background image and resize it."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=8) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    img = Image.open(io.BytesIO(data))
                    return img.convert("RGBA").resize((800, 400))
    except Exception as e:
        logger.error(f"Failed to fetch custom background {url}: {e}")
    return None

def get_card_font(font_type: str, size: int) -> ImageFont.ImageFont:
    """Attempt to load clean system fonts in Windows, fallback to default font."""
    font_paths = []
    if font_type == "bold":
        font_paths = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/trebucbd.ttf",
            "C:/Windows/Fonts/impact.ttf"
        ]
    else:
        font_paths = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/trebuc.ttf",
            "C:/Windows/Fonts/cour.ttf"
        ]
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            pass
            
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def draw_procedural_background(style: str, color_theme: str) -> Image.Image:
    """Draw one of 10 stylized backgrounds mapped to 8 color themes (80 combinations total)."""
    theme = THEMES.get(color_theme, THEMES["dark_space"])
    c1 = theme["primary"]
    c2 = theme["secondary"]

    # Base Canvas
    bg = Image.new("RGBA", (800, 400), (15, 23, 42, 255))
    draw = ImageDraw.Draw(bg)

    # 1. Plain Gradient
    if style == "plain_gradient":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))

    # 2. Tech Grid
    elif style == "tech_grid":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        for x in range(0, 800, 40):
            draw.line([(x, 0), (x, 400)], fill=(c1[0], c1[1], c1[2], 30), width=1)
        for y in range(0, 400, 40):
            draw.line([(0, y), (800, y)], fill=(c1[0], c1[1], c1[2], 30), width=1)

    # 3. Cosmic Stars
    elif style == "cosmic_stars":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        random.seed(42)
        for _ in range(80):
            x = random.randint(0, 800)
            y = random.randint(0, 400)
            r = random.randint(1, 3)
            opacity = random.randint(50, 200)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255, opacity))
        for _ in range(5):
            x = random.randint(50, 750)
            y = random.randint(50, 350)
            s = random.randint(5, 12)
            op = random.randint(100, 255)
            draw.line([(x-s, y), (x+s, y)], fill=(255, 255, 255, op), width=1)
            draw.line([(x, y-s), (x, y+s)], fill=(255, 255, 255, op), width=1)

    # 4. Geometric Wires
    elif style == "geometric_wires":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        random.seed(1337)
        pts = [(random.randint(0, 800), random.randint(0, 400)) for _ in range(25)]
        for i, p1 in enumerate(pts):
            draw.ellipse([p1[0]-3, p1[1]-3, p1[0]+3, p1[1]+3], fill=(c1[0], c1[1], c1[2], 120))
            for p2 in pts[i+1:]:
                dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if dist < 160:
                    alpha = int((1 - dist / 160) * 80)
                    draw.line([p1, p2], fill=(c1[0], c1[1], c1[2], alpha), width=1)

    # 5. Wave Lines
    elif style == "wave_lines":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        for w in range(4):
            pts = []
            freq = 0.005 + w * 0.002
            amp = 30 + w * 10
            phase = w * 1.5
            y_offset = 200 + (w - 1.5) * 40
            for x in range(0, 801, 10):
                y = y_offset + math.sin(x * freq + phase) * amp
                pts.append((x, y))
            draw.line(pts, fill=(c2[0], c2[1], c2[2], 50 + w * 20), width=2)

    # 6. Circular Aura
    elif style == "circular_aura":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        aura_img = Image.new("RGBA", (800, 400), (0,0,0,0))
        aura_draw = ImageDraw.Draw(aura_img)
        cx, cy = 400, 140
        for r in range(300, 50, -10):
            alpha = int((1 - r / 300) * 45)
            aura_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(c1[0], c1[1], c1[2], alpha))
        bg = Image.alpha_composite(bg, aura_img)

    # 7. Circuit Board
    elif style == "circuit_board":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        random.seed(999)
        for _ in range(12):
            start_x = random.randint(0, 800)
            start_y = random.randint(0, 400)
            length = random.randint(40, 150)
            direction = random.choice(["H", "V", "D"])
            p1 = (start_x, start_y)
            if direction == "H":
                p2 = (start_x + length, start_y)
            elif direction == "V":
                p2 = (start_x, start_y + length)
            else:
                p2 = (start_x + length, start_y + length)
            draw.line([p1, p2], fill=(c1[0], c1[1], c1[2], 60), width=2)
            draw.ellipse([p2[0]-4, p2[1]-4, p2[0]+4, p2[1]+4], fill=(c2[0], c2[1], c2[2], 180))

    # 8. Retro Synthwave
    elif style == "retro_synthwave":
        for x in range(800):
            f = x / 800.0
            r = int(15 * (1-f) + 40 * f)
            g = int(23 * (1-f) + 18 * f)
            b = int(42 * (1-f) + 36 * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        
        # Sun
        sun_img = Image.new("RGBA", (800, 400), (0,0,0,0))
        sun_draw = ImageDraw.Draw(sun_img)
        sun_r = 90
        sun_cx, sun_cy = 400, 200
        sun_color = (251, 113, 133, 255)
        sun_draw.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r], fill=sun_color)
        for y in range(sun_cy - sun_r, sun_cy + sun_r, 10):
            stripe_h = int((y - (sun_cy - sun_r)) / 22) + 2
            sun_draw.rectangle([0, y, 800, y + stripe_h], fill=(0,0,0,0))
        bg = Image.alpha_composite(bg, sun_img)
        
        # Perspective Grid
        grid_y = 220
        for i in range(12):
            y = grid_y + int(180 * (i / 11) ** 2)
            draw.line([(0, y), (800, y)], fill=(236, 72, 153, 60), width=1)
        vanishing = (400, grid_y)
        for x_start in range(-400, 1200, 80):
            draw.line([vanishing, (x_start, 400)], fill=(236, 72, 153, 50), width=1)

    # 9. Minimalist Frame
    elif style == "minimalist_frame":
        for x in range(800):
            f = x / 800.0
            r = int(20 * (1-f) + 30 * f)
            g = int(24 * (1-f) + 35 * f)
            b = int(33 * (1-f) + 45 * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        
        border_margin = 25
        draw.rectangle(
            [border_margin, border_margin, 800 - border_margin, 400 - border_margin],
            outline=(c1[0], c1[1], c1[2], 100),
            width=2
        )
        size = 15
        for cx, cy in [(25, 25), (775, 25), (25, 375), (775, 375)]:
            hx_dir = 1 if cx == 25 else -1
            draw.line([(cx, cy), (cx + hx_dir * size, cy)], fill=(c1[0], c1[1], c1[2], 255), width=3)
            vy_dir = 1 if cy == 25 else -1
            draw.line([(cx, cy), (cx, cy + vy_dir * size)], fill=(c1[0], c1[1], c1[2], 255), width=3)

    # 10. Abstract Splatter
    elif style == "abstract_splatter":
        for x in range(800):
            f = x / 800.0
            r = int(c1[0] * (1-f) + c2[0] * f)
            g = int(c1[1] * (1-f) + c2[1] * f)
            b = int(c1[2] * (1-f) + c2[2] * f)
            draw.line([(x, 0), (x, 400)], fill=(r, g, b, 255))
        random.seed(777)
        splat_img = Image.new("RGBA", (800, 400), (0,0,0,0))
        splat_draw = ImageDraw.Draw(splat_img)
        for _ in range(15):
            cx = random.randint(0, 800)
            cy = random.randint(0, 400)
            r = random.randint(60, 130)
            c = random.choice([c1, c2])
            splat_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(c[0], c[1], c[2], 40))
        splat_img = splat_img.filter(ImageFilter.BoxBlur(20))
        bg = Image.alpha_composite(bg, splat_img)

    return bg

def _generate_card_sync(
    avatar_img: Image.Image,
    bg_img: Image.Image,
    username: str,
    server_name: str,
    member_count: str,
    custom_text: str,
    config: dict
) -> io.BytesIO:
    """Synchronously perform all PIL drawing, card building, and PNG encoding operations."""
    image_style = config.get("image_style", "plain_gradient")
    image_color = config.get("image_color", "cyan_neon")

    if bg_img is None:
        bg_img = draw_procedural_background(image_style, image_color)

    # Get active elements flags
    elements = config.get("image_elements", {})
    show_avatar = elements.get("avatar", True)
    show_username = elements.get("username", True)
    show_server = elements.get("server_name", True)
    show_count = elements.get("member_count", True)

    draw = ImageDraw.Draw(bg_img)
    theme = THEMES.get(image_color, THEMES["cyan_neon"])
    primary_color = theme["primary"]

    # Draw Avatar
    avatar_y = 140
    if show_avatar and avatar_img:
        avatar_img = avatar_img.convert("RGBA").resize((120, 120))
        mask = Image.new("L", (120, 120), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, 120, 120], fill=255)

        round_avatar = ImageOps.fit(avatar_img, (120, 120), centering=(0.5, 0.5))
        round_avatar.putalpha(mask)
        bg_img.paste(round_avatar, (340, avatar_y - 60), round_avatar)

        # Glow Ring and Border
        draw.ellipse([338, avatar_y - 62, 462, avatar_y + 62], outline=(primary_color[0], primary_color[1], primary_color[2], 255), width=3)
        draw.ellipse([334, avatar_y - 66, 466, avatar_y + 66], outline=(primary_color[0], primary_color[1], primary_color[2], 60), width=1)

    # Draw Text Layers
    title_font = get_card_font("bold", 30)
    sub_font = get_card_font("regular", 20)
    minor_font = get_card_font("regular", 15)

    current_y = avatar_y + 80 if show_avatar else 100

    if show_username and username:
        try:
            w = draw.textlength(username, font=title_font)
        except AttributeError:
            w = len(username) * 14
        draw.text((400 - w/2, current_y), username, fill=(255, 255, 255, 255), font=title_font)
        current_y += 45

    if show_server and server_name:
        server_text = f"Welcome to {server_name}"
        try:
            w = draw.textlength(server_text, font=sub_font)
        except AttributeError:
            w = len(server_text) * 9
        draw.text((400 - w/2, current_y), server_text, fill=(primary_color[0], primary_color[1], primary_color[2], 230), font=sub_font)
        current_y += 30

    if show_count and member_count:
        count_text = f"Member #{member_count}"
        try:
            w = draw.textlength(count_text, font=minor_font)
        except AttributeError:
            w = len(count_text) * 7
        draw.text((400 - w/2, current_y), count_text, fill=(200, 200, 200, 180), font=minor_font)
        current_y += 25

    if custom_text:
        try:
            w = draw.textlength(custom_text, font=minor_font)
        except AttributeError:
            w = len(custom_text) * 7
        draw.text((400 - w/2, current_y), custom_text, fill=(primary_color[0], primary_color[1], primary_color[2], 255), font=minor_font)

    img_byte_arr = io.BytesIO()
    bg_img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr


async def generate_welcome_goodbye_card(
    avatar_url: str,
    username: str,
    server_name: str,
    member_count: str,
    custom_text: str,
    config: dict
) -> io.BytesIO:
    """Generate the complete customized Image Card asynchronously by calling the sync renderer in a thread."""
    elements = config.get("image_elements", {})
    show_avatar = elements.get("avatar", True)
    custom_bg_url = config.get("custom_bg_url", "")

    avatar_img = None
    if show_avatar and avatar_url:
        avatar_img = await fetch_avatar(avatar_url)

    bg_img = None
    if custom_bg_url:
        bg_img = await fetch_custom_bg(custom_bg_url)

    # Offload the synchronous rendering to a thread pool
    return await asyncio.to_thread(
        _generate_card_sync,
        avatar_img,
        bg_img,
        username,
        server_name,
        member_count,
        custom_text,
        config
    )



# ---------------------------------------------------------------------------
# Cog Class Implementation
# ---------------------------------------------------------------------------
class WelcomeHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "👋 KAIZER K5 - Welcome & Goodbye System (Page 1/2)",
                "description": "Greet or send off members with fully customizable graphics and text.",
                "fields": [
                    {"name": "• Configuration Dashboard", "value": "Welcome and Goodbye channels, enable switches, and custom raw JSON templates are managed via the web dashboard at: `http://localhost:8000` (or host IP)."},
                    {"name": "• Placeholders Supported", "value": "Use these placeholders in your custom welcome/goodbye messages:\n"
                                                      "- `{user}`: Mentions the joining/leaving member.\n"
                                                      "- `{username}`: The member's Discord username.\n"
                                                      "- `{server}`: The server's name.\n"
                                                      "- `{member_count}`: The updated member count.\n"
                                                      "- `{avatar_url}`: URL of the member's profile picture."}
                ]
            },
            # Page 2
            {
                "title": "🎨 KAIZER K5 - Image Cards & Themes (Page 2/2)",
                "description": "Customize procedural image cards dynamically generated for alerts.",
                "fields": [
                    {"name": "• Color Themes", "value": "Available color themes: `cyan_neon`, `red_hot`, `emerald_green`, `golden_hour`, `electric_purple`, `synthwave_pink`, `dark_space`, `ice_blue`"},
                    {"name": "• Procedural Layout Styles", "value": "Choose from 10 abstract background styles:\n"
                                                    "`plain_gradient`, `tech_grid`, `cosmic_stars`, `geometric_wires`, `wave_lines`, `circular_aura`, `circuit_board`, `retro_synthwave`, `minimalist_frame`, `abstract_splatter`"},
                    {"name": "• Custom Backdrops", "value": "Provide a direct image URL under `custom_bg_url` in your dashboard config to use a custom background image."}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0xEC4899
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


class WelcomeGoodbyeCog(commands.Cog, name="WelcomeGoodbye"):
    """Handles sending highly customized welcome/goodbye channel alerts, generated cards, and DMs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="welcome", description="Show welcome & goodbye configuration help.")
    async def welcome_command(self, ctx: commands.Context):
        view = WelcomeHelpView(ctx.author.id)
        msg = await ctx.send(embed=view.make_embed(), view=view)
        view.message = msg

    def replace_placeholders(self, text: str, member: discord.Member) -> str:
        if not text:
            return ""
        return (
            text.replace("{user}", member.mention)
            .replace("{username}", member.name)
            .replace("{server}", member.guild.name)
            .replace("{member_count}", str(member.guild.member_count))
            .replace("{avatar_url}", str(member.display_avatar.url))
        )

    async def send_welcome_goodbye(self, member: discord.Member, is_join: bool, force: bool = False):
        guild_id = str(member.guild.id)
        settings = await asyncio.to_thread(db_client.get_guild_settings, guild_id)
        if not settings:
            if force:
                raise ValueError("No settings found in the database for this server.")
            return

        enabled_key = "welcome_enabled" if is_join else "goodbye_enabled"
        channel_key = "welcome_channel" if is_join else "goodbye_channel"
        msg_key = "welcome_message" if is_join else "goodbye_message"

        master_enabled = settings.get(enabled_key, False)
        if not master_enabled and not force:
            return

        # ---------------------------------------------------------------------------
        # 1. Parse JSON configuration
        # ---------------------------------------------------------------------------
        raw_msg = settings.get(msg_key, "")
        if not raw_msg:
            if force:
                raise ValueError(f"No {'welcome' if is_join else 'goodbye'} message configured. Please save your settings first.")
            return

        config_dict = {}
        is_rich_config = False
        try:
            config_dict = json.loads(raw_msg)
            if isinstance(config_dict, dict):
                is_rich_config = True
        except json.JSONDecodeError:
            pass

        # Resolve values based on schema mapping
        message_type = "text"
        txt_content = raw_msg
        embed_data = None
        image_enabled = False
        dm_enabled = False
        dm_type = "text"
        dm_txt_content = ""
        dm_embed_data = None

        if is_rich_config:
            # New Rich Configuration Schema
            if "message_type" in config_dict:
                message_type = config_dict.get("message_type", "text")
                txt_content = config_dict.get("text", "")
                embed_data = config_dict.get("embed")
                image_enabled = config_dict.get("image_enabled", False)
                dm_enabled = config_dict.get("dm_enabled", False)
                dm_type = config_dict.get("dm_type", "text")
                dm_txt_content = config_dict.get("dm_text", "")
                dm_embed_data = config_dict.get("dm_embed")
            # Old Embedded Message Schema
            elif config_dict.get("embed", False):
                message_type = "embed"
                embed_data = config_dict

        # ---------------------------------------------------------------------------
        # 2. Dispatch to Guild Text Channel
        # ---------------------------------------------------------------------------
        channel_id_str = settings.get(channel_key)
        channel = None
        if channel_id_str:
            try:
                channel_id = int(channel_id_str)
                channel = member.guild.get_channel(channel_id)
            except ValueError:
                logger.error(f"Invalid channel ID stored for {channel_key}: {channel_id_str}")

        if force:
            if not channel_id_str and not dm_enabled:
                raise ValueError("Neither a channel alert nor a DM configuration is set/enabled.")
            if channel_id_str and not channel:
                raise ValueError(f"Could not find or access the selected channel ID {channel_id_str}. Verify the bot is in the server and can see the channel.")

        if channel and message_type != "none":
            cleaned_msg = ""
            embed = None
            file = None

            # Resolve plain text
            if message_type == "text" and txt_content:
                cleaned_msg = self.replace_placeholders(txt_content, member)

            # Resolve Embed
            elif message_type == "embed" and embed_data:
                title = self.replace_placeholders(embed_data.get("title", ""), member)
                desc = self.replace_placeholders(embed_data.get("description", ""), member)
                footer_text = self.replace_placeholders(embed_data.get("footer", ""), member)
                footer_icon = self.replace_placeholders(embed_data.get("footer_icon", ""), member)
                thumbnail = self.replace_placeholders(embed_data.get("thumbnail", ""), member)
                image = self.replace_placeholders(embed_data.get("image", ""), member)
                color_hex = embed_data.get("color", "#0affe4").replace("#", "")
                
                try:
                    color_val = int(color_hex, 16)
                except ValueError:
                    color_val = 0x0affe4

                embed = discord.Embed(color=color_val)
                if title:
                    embed.title = title
                if desc:
                    embed.description = desc
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                if image:
                    embed.set_image(url=image)
                if footer_text:
                    embed.set_footer(text=footer_text, icon_url=footer_icon if footer_icon else None)
                elif footer_icon:
                    embed.set_footer(icon_url=footer_icon)

            # Resolve Image Card
            if image_enabled:
                try:
                    custom_overlay = self.replace_placeholders(config_dict.get("image_elements", {}).get("custom_text", ""), member)
                    img_buffer = await generate_welcome_goodbye_card(
                        avatar_url=str(member.display_avatar.url),
                        username=member.name,
                        server_name=member.guild.name,
                        member_count=str(member.guild.member_count),
                        custom_text=custom_overlay,
                        config=config_dict
                    )
                    filename = "welcome.png" if is_join else "goodbye.png"
                    file = discord.File(img_buffer, filename=filename)
                    if embed:
                        embed.set_image(url=f"attachment://{filename}")
                except Exception as e:
                    logger.error(f"Failed to generate PIL image card: {e}")

            # Send payload
            try:
                if embed:
                    if file:
                        await channel.send(embed=embed, file=file)
                    else:
                        await channel.send(embed=embed)
                elif cleaned_msg or file:
                    if file:
                        await channel.send(content=cleaned_msg, file=file)
                    else:
                        await channel.send(content=cleaned_msg)
                logger.info(f"Dispatched {'welcome' if is_join else 'goodbye'} channel message for {member.name} in #{channel.name}")
            except discord.Forbidden as err:
                logger.warning(f"Missing permissions to send welcome/goodbye alert in #{channel.name}")
                if force:
                    raise ValueError(f"Missing permissions to send messages/files in #{channel.name}.")
            except Exception as e:
                logger.error(f"Error sending welcome/goodbye alert to #{channel.name}: {e}")
                if force:
                    raise ValueError(f"Failed to send channel message: {e}")

        # ---------------------------------------------------------------------------
        # 3. Send Direct Message (DM) to Member
        # ---------------------------------------------------------------------------
        if dm_enabled:
            dm_msg = ""
            dm_embed = None

            if dm_type == "text" and dm_txt_content:
                dm_msg = self.replace_placeholders(dm_txt_content, member)
            elif dm_type == "embed" and dm_embed_data:
                title = self.replace_placeholders(dm_embed_data.get("title", ""), member)
                desc = self.replace_placeholders(dm_embed_data.get("description", ""), member)
                footer_text = self.replace_placeholders(dm_embed_data.get("footer", ""), member)
                footer_icon = self.replace_placeholders(dm_embed_data.get("footer_icon", ""), member)
                thumbnail = self.replace_placeholders(dm_embed_data.get("thumbnail", ""), member)
                image = self.replace_placeholders(dm_embed_data.get("image", ""), member)
                color_hex = dm_embed_data.get("color", "#0affe4").replace("#", "")
                
                try:
                    color_val = int(color_hex, 16)
                except ValueError:
                    color_val = 0x0affe4

                dm_embed = discord.Embed(color=color_val)
                if title:
                    dm_embed.title = title
                if desc:
                    dm_embed.description = desc
                if thumbnail:
                    dm_embed.set_thumbnail(url=thumbnail)
                if image:
                    dm_embed.set_image(url=image)
                if footer_text:
                    dm_embed.set_footer(text=footer_text, icon_url=footer_icon if footer_icon else None)
                elif footer_icon:
                    dm_embed.set_footer(icon_url=footer_icon)

            if dm_msg or dm_embed:
                try:
                    # Create DM channel
                    dm_channel = member.dm_channel or await member.create_dm()
                    if dm_embed:
                        await dm_channel.send(embed=dm_embed)
                    else:
                        await dm_channel.send(dm_msg)
                    logger.info(f"Dispatched DM {'welcome' if is_join else 'goodbye'} to {member.name}")
                except discord.Forbidden:
                    logger.info(f"Cannot send DM to {member.name} (DMs closed)")
                    if force:
                        raise ValueError("Failed to send DM: Your DMs are closed or you blocked the bot.")
                except Exception as e:
                    logger.error(f"Failed to send DM to {member.name}: {e}")
                    if force:
                        raise ValueError(f"Failed to send DM message: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"Member joined: {member.name} in guild {member.guild.name}")
        await self.send_welcome_goodbye(member, is_join=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        logger.info(f"Member left: {member.name} in guild {member.guild.name}")
        await self.send_welcome_goodbye(member, is_join=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeGoodbyeCog(bot))
