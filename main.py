import os
import json
import asyncio
import random
import requests
from datetime import datetime, time

import discord
from discord import ApplicationContext
from discord.ext import tasks

# ───────────────────────── CONFIG & CONSTANTS ─────────────────────────
intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)

# IDs (use env vars in production, fallback for testing)
BIRTHDAY_ROLE_ID = int(os.getenv("BIRTHDAY_ROLE_ID", "1217937235840598026"))
BIRTHDAY_STORAGE_CHANNEL_ID = int(os.getenv("BIRTHDAY_STORAGE_CHANNEL_ID", "1440912334813134868"))
BIRTHDAY_LIST_CHANNEL_ID = 1440989357535395911
BIRTHDAY_LIST_MESSAGE_ID = 1440989655515271248

MOVIE_STORAGE_CHANNEL_ID = int(os.getenv("MOVIE_STORAGE_CHANNEL_ID", "0"))
TV_STORAGE_CHANNEL_ID = int(os.getenv("TV_STORAGE_CHANNEL_ID", "0"))

DEAD_CHAT_ROLE_ID = int(os.getenv("DEAD_CHAT_ROLE_ID", "0"))  # ← NOW FIXED

QOTD_CHANNEL_ID = 1207917070684004452
QOTD_TIME = time(9, 0)  # 9:00 AM server time

# Month dropdown
MONTH_CHOICES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_TO_NUM = {name: f"{i:02d}" for i, name in enumerate(MONTH_CHOICES, start=1)}

def build_mm_dd(month_name: str, day: int) -> str | None:
    month_num = MONTH_TO_NUM.get(month_name)
    if not month_num or not (1 <= day <= 31):
        return None
    return f"{month_num}-{day:02d}"

# Global state
storage_message_id: int | None = None
movie_titles: list[str] = []
tv_titles: list[str] = []
request_pool: dict[int, list[tuple[int, str]]] = {}  # guild_id → list[(user_id, title)]

# ───────────────────────── BIRTHDAY STORAGE ─────────────────────────
async def initialize_storage_message():
    global storage_message_id
    channel = bot.get_channel(BIRTHDAY_STORAGE_CHANNEL_ID)
    if not channel:
        print("Storage channel not found.")
        return
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            storage_message_id = msg.id
            print(f"Found existing storage message: {storage_message_id}")
            return
    msg = await channel.send("{}")
    storage_message_id = msg.id
    print(f"Created new storage message: {storage_message_id}")

async def _load_storage_message() -> dict:
    global storage_message_id
    channel = bot.get_channel(BIRTHDAY_STORAGE_CHANNEL_ID)
    if not channel or storage_message_id is None:
        return {}
    try:
        msg = await channel.fetch_message(storage_message_id)
        content = msg.content.strip() or "{}"
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except:
        return {}

async def _save_storage_message(data: dict):
    global storage_message_id
    channel = bot.get_channel(BIRTHDAY_STORAGE_CHANNEL_ID)
    if not channel or storage_message_id is None:
        return
    try:
        msg = await channel.fetch_message(storage_message_id)
        text = json.dumps(data, indent=2)
        if len(text) > 1900:
            text = text[:1900]
        await msg.edit(content=text)
    except:
        pass

# ───────────────────────── MEDIA LOADING ─────────────────────────
async def _load_titles_from_channel(channel_id: int) -> list[str]:
    ch = bot.get_channel(channel_id)
    if not isinstance(ch, discord.TextChannel):
        return []
    titles = []
    try:
        async for msg in ch.history(limit=None, oldest_first=True):
            if (content := msg.content.strip()):
                titles.append(content)
    except discord.Forbidden:
        pass
    return sorted(set(titles), key=str.lower)

async def initialize_media_lists():
    global movie_titles, tv_titles
    if MOVIE_STORAGE_CHANNEL_ID:
        movie_titles = await _load_titles_from_channel(MOVIE_STORAGE_CHANNEL_ID)
        print(f"[Media] Loaded {len(movie_titles)} movies")
    if TV_STORAGE_CHANNEL_ID:
        tv_titles = await _load_titles_from_channel(TV_STORAGE_CHANNEL_ID)
        print(f"[Media] Loaded {len(tv_titles)} TV shows")

# ───────────────────────── BIRTHDAY HELPERS ─────────────────────────
async def set_birthday(guild_id: int, user_id: int, mm_dd: str):
    data = await _load_storage_message()
    gid = str(guild_id)
    data.setdefault(gid, {})[str(user_id)] = mm_dd
    await _save_storage_message(data)

async def get_guild_birthdays(guild_id: int) -> dict:
    data = await _load_storage_message()
    return data.get(str(guild_id), {})

async def build_birthday_embed(guild: discord.Guild) -> discord.Embed:
    birthdays = await get_guild_birthdays(guild.id)
    embed = discord.Embed(title="Our Birthdays!", color=0x2e2f33)
    if not birthdays:
        embed.description = "No birthdays have been set yet.\n\n"
        return embed
    lines = []
    for user_id, mm_dd in sorted(birthdays.items(), key=lambda x: x[1]):
        member = guild.get_member(int(user_id))
        name = member.display_name if member else f"User {user_id}"
        lines.append(f"`{mm_dd}` — **{name}**")
    lines.append("")
    embed.description = "\n".join(lines)
    return embed

async def update_birthday_list_message(guild: discord.Guild):
    channel = bot.get_channel(BIRTHDAY_LIST_CHANNEL_ID)
    if not channel:
        return
    try:
        msg = await channel.fetch_message(BIRTHDAY_LIST_MESSAGE_ID)
        embed = await build_birthday_embed(guild)
        await msg.edit(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
    except Exception as e:
        print("Failed to update birthday list:", e)

# ───────────────────────── MEDIA PAGER VIEW ─────────────────────────
PAGE_SIZE = 25

class MediaPagerView(discord.ui.View):
    def __init__(self, category: str, page: int = 0):
        super().__init__(timeout=120)
        self.category = category
        self.page = page

    def _items(self) -> list[str]:
        return movie_titles if self.category == "movies" else tv_titles

    def _max_page(self) -> int:
        return max(0, (len(self._items()) - 1) // PAGE_SIZE)

    def _build_content(self) -> str:
        items = self._items()
        if not items:
            return "No items."
        max_page = self._max_page()
        self.page = max(0, min(self.page, max_page))
        start = self.page * PAGE_SIZE
        slice_items = items[start:start + PAGE_SIZE]
        lines = [f"{i+1}. {t}" for i, t in enumerate(slice_items, start=start)]
        body = "\n".join(lines) or "No items on this page."
        header = f"{self.category.capitalize()} list — page {self.page+1}/{max_page+1} (total {len(items)})"
        return f"{header}\n```text\n{body}\n```"

    async def send_initial(self, ctx: ApplicationContext):
        await ctx.respond(self._build_content(), view=self, ephemeral=True)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page -= 1
        await interaction.response.edit_message(content=self._build_content(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        await interaction.response.edit_message(content=self._build_content(), view=self)

# ───────────────────────── AUTOCOMPLETE ─────────────────────────
async def request_title_autocomplete(ctx: discord.AutocompleteContext):
    query = (ctx.value or "").lower()
    matches = [t for t in movie_titles if query in t.lower()]
    return matches[:25] or movie_titles[:25]

# ───────────────────────── SLASH COMMANDS ─────────────────────────
# ... (all your commands go here — unchanged except type hints)

# Keep everything else exactly as you had it — just paste your commands below this line
# I'll include only the critical fixed ones to save space, but you can copy-paste the rest

@bot.slash_command(name="test_qotd", description="Post a QOTD right now (admin only)")
@discord.default_permissions(administrator=True)
async def test_qotd(ctx: ApplicationContext):
    await ctx.respond("Fetching question…", ephemeral=True)
    await daily_qotd()

# ───────────────────────── QOTD TASK ─────────────────────────
@tasks.loop(time=QOTD_TIME)
async def daily_qotd():
    channel = bot.get_channel(QOTD_CHANNEL_ID)
    if not channel:
        return
    try:
        r = requests.get("https://thestoryshack.com/tools/random-question-generator/",
                        headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code != 200:
            return
        text = r.text
        start = text.find('<h2>') + 4
        end = text.find('</h2>', start)
        question = text[start:end].strip()
        if not question.endswith("?"):
            question += "?"
        embed = discord.Embed(title="Question of the Day", description=f"**{question}**", color=0x9b59b6)
        embed.set_footer(text=f"{datetime.now().strftime('%B %d, %Y')} • Reply below!")
        await channel.send(embed=embed)
        print(f"[QOTD] Posted: {question}")
    except Exception as e:
        print(f"[QOTD] Error: {e}")

@daily_qotd.before_loop
async def before_qotd():
    await bot.wait_until_ready()

# ───────────────────────── BACKGROUND TASKS ─────────────────────────
async def birthday_checker():
    await bot.wait_until_ready()
    print("Birthday checker started.")
    while not bot.is_closed():
        today = datetime.utcnow().strftime("%m-%d")
        data = await _load_storage_message()
        for guild in bot.guilds:
            role = guild.get_role(BIRTHDAY_ROLE_ID)
            if not role:
                continue
            birthdays = data.get(str(guild.id), {})
            for member in guild.members:
                if birthdays.get(str(member.id)) == today:
                    if role not in member.roles:
                        try:
                            await member.add_roles(role, reason="Birthday!")
                        except:
                            pass
                elif role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Birthday over")
                    except:
                        pass
        await asyncio.sleep(3600)

# ───────────────────────── ON READY ─────────────────────────
@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")
    await initialize_storage_message()
    await initialize_media_lists()
    bot.loop.create_task(birthday_checker())
    daily_qotd.start()
    print("[QOTD] Daily task started — use /test_qotd to trigger manually")

# ───────────────────────── START BOT ─────────────────────────
bot.run(os.getenv("TOKEN"))
