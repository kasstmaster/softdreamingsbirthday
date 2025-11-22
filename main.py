import os
import json
import asyncio
from datetime import datetime

import discord
import random  # for random picks

intents = discord.Intents.default()
intents.members = True 

bot = discord.Bot(intents=intents)

BIRTHDAY_ROLE_ID = int(os.getenv("BIRTHDAY_ROLE_ID", "1217937235840598026"))
BIRTHDAY_STORAGE_CHANNEL_ID = int(os.getenv("BIRTHDAY_STORAGE_CHANNEL_ID", "1440912334813134868"))
BIRTHDAY_LIST_CHANNEL_ID = 1440989357535395911
BIRTHDAY_LIST_MESSAGE_ID = 1440989655515271248
MOVIE_REQUESTS_CHANNEL_ID = int(os.getenv("MOVIE_REQUESTS_CHANNEL_ID", "0"))

# New: separate storage channels for movies / TV shows
MOVIE_STORAGE_CHANNEL_ID = int(os.getenv("MOVIE_STORAGE_CHANNEL_ID", "0"))
TV_STORAGE_CHANNEL_ID    = int(os.getenv("TV_STORAGE_CHANNEL_ID", "0"))

storage_message_id: int | None = None

# In-memory media lists
movie_titles: list[str] = []
tv_titles: list[str] = []


# ────────────────────── RAW MASTER MEDIA LIST (YOUR FULL LIST) ──────────────────────

RAW_MEDIA_LIST = """
0-A
The 100 - TV SHOW
13 Going On 30 (2004)
1883- TV SHOW
1984 (1984)
30 Days of Night (2007)
300 (2006)
300 Rise of an Empire (2014)
310 to Yuma (2007)
The 40-Year-Old Virgin (2005)
50 First Dates (2004)
9 (2009)
The Addams Family - TV SHOW
Adventures In Babysitting (1987)
Alien (1979)
Alien Covenant (2017)
Alien Romulus (2024)
Alien Earth - TV SHOW
Aliens (1986)
Alita Battle Angel (2019)
All Dogs Go To Heaven (1989)
Allegiant (2016)
American Pie - Reunion (2012)
American Pie Unrated (1999)
An American Tail (1986)
An American Tail Fievel Goes West (1991)
Anastasia (1997)
The Andy Griffith Show - TV SHOW
Annihilation (2018)
Ant-Man (2015)
Ant-Man And The Wasp (2018)
Apocalypto (2006)
Apollo 13 (1995)
Armageddon (1998)
Arrival (2016)
Artificial Intelligence (2001)
Austin Powers in Goldmember (2002)
Austin Powers International Man of Mystery (1997)
Austin Powers The Spy Who Shagged Me (1999)
The Avengers (2012)
Avengers Age of Ultron (2015)
Avengers Endgame (2019)
Avengers Infinity War (2018) 
B
Babe (1995)
Back to the Future 1 (1985)
Back to the Future 2 (1989)
Back to the Future 3 (1990)
Balto (1995)
BASEketball (1998)
The Batman (2022)
Batman - The Dark Knight (2008)
Batman - The Dark Knight Rises (2012)
Batman Begins (2005)
The Beach (2000)
Beauty and the Beast (1991)
Beetlejuice (1988)
Being Human (UK) - TV SHOW
Better Off Dead (1985)
Big Fish (2003)
Big Trouble In Little China (1986)
Bill and Ted Face the Music (2020)
Bill and Ted's Bogus Journey (1991)
Bill and Ted's Excellent Adventure (1989)
Bio-Dome (1996)
Black Hawk Down (2001)
Black Panther (2018)
Black Sheep (1996)
Blade (1998)
Blade II (2002)
Blade Runner 2049 (2017)
Blast from the Past (1999)
Bone Tomahawk (2015)
The Book of Eli (2010)
The Boondock Saints Director's Cut (1999)
Braveheart (1995)
The Breakfast Club (1985)
The Butterfly Effect (2004) 
C
The Cabin in the Woods (2011)
The Cable Guy (1996)
Captain America - The First Avenger (2011)
Captain America Civil War (2016)
Captain America The Winter Soldier (2014)
Captain Marvel (2019)
Captain Underpants The First Epic Movie (2017)
Carriers (2009)
Castle - TV SHOW
Chicago PD - TV SHOW
Children of Men (2006)
The Chosen - TV SHOW
A Christmas Story (1983)
Christmas Vacation (1989)
Cinderella (1950)
Clerks 2 (2006) [1080p]
Clerks THEATRICAL (1994)
Click (2006)
Coco (2017)
Columbo - TV SHOW
Coneheads (1993)
The Conjuring (2013)
The Conjuring 2 (2016)
The Conjuring The Devil Made Me Do It (2021)
Constantine (2005)
Coraline (2009)
The Core (2003)
The Creator (2023)
Creed II (2018)
Crocodile Dundee (1986)
The Crow (1994) 
D
D2 The Mighty Ducks (1994)
Dances with Wolves (1990)
Dante's Peak (1997)
Dark - TV SHOW
Dawn of the Dead (2004)
Dawn of the Planet of the Apes (2014)
The Day After Tomorrow (2004)
The Day The Earth Stood Still (1951)
Dazed and Confused (1993)
Deadpool 2 (2018)
Deadpool and Wolverine (2024)
Death Becomes Her (1992)
Death of a Nation (2018)
Death Of A Unicorn (2025)
Deep Impact (1998)
Demolition Man (1993)
Die Hard (1998)
Dinosaurs - TV SHOW
Dirty Dancing (1987)
Divergent (2014)
Doctor Detroit (1983)
Doctor Strange (2016)
Dodgeball A True Underdog Story (2004)
Dogma (1999)
Don't Be A Menace To South Central While Drinking Your Juice In The Hood (1996)
Don't Tell Mom The Babysitter's Dead (1991)
Donnie Darko DIRECTORS CUT (2001)
Doug - TV SHOW
DOUG's 1st Movie (1999)
Dumb and Dumber (1994)
Dune (2021)
Dune Part Two (2024)
Dungeons and Dragons Honor Among Thieves (2023) 
E
Edge of Tomorrow (2014)
Edward Scissorhands (1990)
Eight Legged Freaks (2002)
Elf (2003)
Elysium (2013)
The Emperor's New Groove (2000)
The Equalizer (2014)
Eternal Sunshine of the Spotless Mind (2004)
Ever After (1998)
The Evil Dead (1981)
Evil Dead (2013)
Evil Dead - Army of Darkness (1992)
Evil Dead II (1987)
Excalibur (1981)
Explorers (1985) 
F
Fallout - TV SHOW
The Fast and the Furious (2001)
FernGully The Last Rainforest (1992)
The Fifth Element Remastered (1997)
Final Destination (2000)
The Final Destination (2009)
Final Destination 2 (2003)
Final Destination 3 (2006)
Final Destination 5 (2011)
Final Destination Bloodlines (2025)
Firefly - TV SHOW
Flight of the Navigator (1986)
The Flintstones - TV SHOW
The Flintstones (1994)
The Flintstones in Viva Rock Vegas (2000)
Friday (1995)
Friday After Next (2002)
Fury (2014) 
G
Galaxy Quest (1999)
Game of Thrones - TV SHOW
George Of The Jungle (1997)
Ghostbusters (1984)
Ghostbusters Afterlife (2021)
Gladiator (2000)
Godzilla King Of The Monsters (2019)
Godzilla Minus One (2023)
Godzilla Vs
Godzilla X Kong The New Empire (2024)
The Golden Child (1986)
A Goofy Movie (1995)
The Goonies (1985)
Groundhog Day (1993)
The Grudge (2004)
Grumpier Old Men (1995)
Grumpy Old Men (1993)
Guardians of the Galaxy (2014)
Guardians Of The Galaxy Vol
Guardians of the Galaxy Vol 2 (2017)
Guillermo Del Toro's Pinocchio (2022)
Guyver the Dark Hero (1994) 
H
Hackers (1995)
Harold & Kumar Escape From Guantanamo Bay (2008)
Harold & Kumar Go To White Castle (2004)
Harry and the Hendersons (1987)
Hawaii Five-0 - TV SHOW
Hell And Back (2015)
Hellboy (2004)
Hellboy The Golden Army (2008)
The Hitchhiker's Guide To The Galaxy
The Hitchhiker's Guide to the Galaxy (2005)
The Hobbit An Unexpected Journey EXTENDED (2012)
The Hobbit The Battle of the Five Armies EXTENDED (2014)
The Hobbit The Desolation of Smaug EXTENDED (2013)
Home Alone (1990)
Homeward Bound The Incredible Journey (1993)
Honey, I Shrunk The Kids (1989)
Hook (1991)
The Hot Chick (2002)
Hot Fuzz (2007)
Hot Shots (1991)
Hot Shots Part Deux (1993)
Hot Tub Time Machine (2010)
Howl's Moving Castle (2004)
Hulk (2003)
The Hunger Games (2012)
The Hunger Games Catching Fire (2013)
The Hunger Games Mockingjay Part 1 (2014)
The Hunger Games Mockingjay Part 2 (2015)
The Hunger Games The Ballad of Songbirds and Snakes (2023) 
I
I Am Mother (2019)
Idiocracy (2006)
Idle Hands (1999)
In The Army Now (1994)
The Incredibles 2004
Independence Day (1996)
Indiana Jones and the Raiders of the Lost Ark (1981)
Inglourious Basterds (2009)
Innerspace (1987)
Insurgent (2015)
Interstellar (2014)
Inuyasha - TV SHOW
The Iron Giant (1999) Director's cut
Iron Man (2008)
Iron Man 2 (2010)
Iron Man 3 (2013)
The Island (2005)
IT (2017)
IT Chapter Two (2019)
It's A Wonderful Life (1946) 
J
Jaws (1975)
Joe Dirt (2001)
John Wick (2014)
John Wick Chapter 2 (2017)
John Wick Chapter 3 - Parabellum (2019)
John Wick Chapter 4 (2023)
Johnny Tsunami (1999)
Jumanji (1995)
Jumper (2008)
Jungle (2017)
Jurassic Park (1993)
Just Before I Go (2014) 
K
The Karate Kid (1984)
The Karate Kid Part 2 (1986)
Kill Bill Vol 1 (2003)
Kill Bill Vol 2 (2004)
Kindergarten Cop (1990)
King Arthur Legend Of The Sword (2017)
Kingdom of the Planet of the Apes (2024)
King of the Hill - TV SHOW
Kingpin (1996)
A Knights Tale (2001)
KPop Demon Hunters (2025)
Kull The Conqueror (1997) 
L
Ladder 49 (2004)
Last Action Hero (1993)
The Last Samurai (2003)
Leave It To Beaver - TV SHOW
Legally Blonde (2001)
Lilo and Stitch (2002)
The Lion King (1994)
Little Giants (1994)
Little Miss Sunshine (2006)
Logan (2017)
The Lord of the Rings The Fellowship of the Ring Extended (2001)
The Lord of the Rings The Return of the King Extended (2003)
The Lord of the Rings The Two Towers (2002)
Lords Of Dogtown (2005) 
M
Maggie (2015)
Malignant (2021)
Mallrats (1995)
Man of Steel (2013)
Man On Fire (2004)
Mars Attacks (1996)
The Martian (2015)
The Matrix (1999)
Maverick (1994)
The Maze Runner (2014)
Maze Runner The Death Cure (2018)
Maze Runner The Scorch Trials (2015)
Me Myself and Irene (2000)
Men In Black (1997)
Men In Black 3 (2012)
Men In Black II (2002)
Metalocalypse - The Doomstar Requiem A Klok Opera (2013)
Michael (1996)
The Mighty Ducks (1992)
Minority Report (2002)
Mission Impossible - Fallout (2018)
Monty Python and the Holy Grail (1975)
Moon (2009)
Mortal Kombat (1995)
Mortal Kombat (2021)
Mortal Kombat Legends Scorpions Revenge (2020)
Moulin Rouge! (2001)
Mrs Doubtfire (1993)
The Mummy (1999)
Murder She Wrote - TV SHOW 
N
The Nanny - TV SHOW
Napoleon Dynamite (2004)
National Lampoon's Vegas Vacation (1997)
National Lampoons Vacation (1983)
National Lampoons Van Wilder (2002)
NCIS - TV SHOW
The NeverEnding Story (1984)
Next Friday (2000)
The Nightmare Before Christmas (1993)
Nobody (2021)
Nobody 2 (2025)
Not Another Teen Movie (2001) 
O
Office Space (1999)
The Old Guard (2020)
Once Upon a Time - TV SHOW
One Hundred And One Dalmatians (1961)
Only the Brave (2017)
Orgazmo (1997)
Orphan Black - TV SHOW
The Other Guys (2010)
Outlander - TV SHOW
The Outsiders (1983) 
P
P.S
Pacific Rim (2013)
Pan's Labyrinth (2006)
The Passion of the Christ (2004)
The Patriot Extended Cut (2000)
Payback (1999)
Pirates of the Caribbean - Curse of the Black Pearl (2003)
Pirates of the Caribbean Dead Man's Chest (2006)
Planet Earth - TV SHOW
Pleasantville (1998)
Pokemon The First Movie (1998)
Pokemon Detective Pikachu (2019)
Predator (1987)
The Prestige (2006)
Pretty In Pink (1986)
The Prince Of Egypt (1998)
The Princess Bride (1987)
Princess Mononoke (1997)
Problem Child (1990)
Problem Child 2 (1991)
Prometheus (2012)
Pulp Fiction (1994) 
Q
A Quiet Place (2018)
A Quiet Place Day One (2024)
A Quiet Place Part II (2020) 
R
Radio Flyer (1992)
Rain Man (1988)
Rat Race (2001)]
Reign - TV SHOW
Reign Of Fire (2002)
Resident Evil (2002)
Resident Evil Apocalypse (2004)
Revenge of the Nerds (1984)
Rise of the Planet of the Apes (2011)
Rizzoli and Isles - TV SHOW
The Road (2009)
RoboCop (1987)
Rock-A-Doodle (1991)
Role Models (2008)
Romancing The Stone (1984)]
Romeo + Juliet (1996)
The Rundown (2003)
The Running Man (1987)
Running Scared (2006) 
S
The Sandlot (1993)
Saved (2004)
The Secret Of NIMH (1982)
Seinfeld - TV SHOW
Seeking a Friend For The End of The World (2012)
Serenity (2005)
Shaun of the Dead (2004)
Shin Godzilla (2016)
Short Circuit (1986)
Shrek (2001)
Shrek 2 (2004)
Shutter Island (2010)
Sin City (2005)
Sixteen Candles (1984)
Sleeping Beauty (1959)
Snowpiercer (2013)
Son In Law (1993)
Sonic the Hedgehog (2020)
Sonic The Hedgehog 2 (2022)
South Park - TV SHOW
South Park Joining the Panderverse (2023)
Spider-Man Far From Home (2019)
Spider-Man Homecoming (2017)
Spirited Away (2001)
Stand by Me (1986)
Star Trek (2009)
Star Trek Beyond (2016)
Star Trek First Contact (1996)
Star Trek Generations (1994)
Star Trek II The Wrath of Khan (1982)
Star Trek III The Search for Spock (1984)
Star Trek Insurrection (1998)
Star Trek Into Darkness (2013)
Star Trek IV The Voyage Home (1986)
Star Trek Nemesis (2002)
Star Trek The Motion Picture (1979)
Star Trek V The Final Frontier (1989)
Star Trek VI The Undiscovered Country (1991)
Star Wars (1977)
Star Wars Return of the Jedi (1983)
Star Wars The Empire Strikes Back (1980)
Stardust (2007)
Starman (1984)
Starship Troopers (1997)
Stranger Things - TV SHOW
The Suicide Squad (2021)
Sunshine (2007)
Super 8 (2011)
Super Mario Bros
The Super Mario Bros Movie (2023)
Super Troopers (2001)
Super Troopers 2 (2018)
The Sword in the Stone (1963)
The Swordsman (2021) 
T
Team America Unrated (2004)
Teenage Mutant Ninja Turtles (1990)
Tenet (2020)
The Terminator (1984)
Terminator 2 Judgment Day DC (1991)
Terminator - The Sarah Connor Chronicles - TV SHOW
Theres Something About Mary EXTENDED (1998)
These Final Hours (2013)
They Live (1988)
The Thing (1982)
Thor (2011)
Thor Ragnarok (2017)
Thor the Dark World (2013)
Thumbelina (1994))
The Time Machine (2002)
Titan A.E
Tombstone (1993)
Tommy Boy (1995)
The Tomorrow War (2021)
Top Gun (1986)
Top Gun Maverick (2022)
Total Recall (1990)
Toy Soldiers (1991)
Tremors (1990)
A Troll In Central Park (1994)
Troy (2004)
True Grit (2010)
True Lies (1994)
True Romance (1993)
Tucker And Dale Vs Evil (2010)
Twisters (2024) 
U
Up (2009)
Upgrade (2018) 
V
V for Vendetta (2006)
Vacation (2015)
Venom Let There Be Carnage (2021)
Vikings - TV SHOW 
W
Walk Hard The Dewey Cox Story (2007)
A Walk to Remember (2002)
War for the planet of the apes (2017)
War of the Worlds (2005)
WarGames (1983)
Waynes World (1992)
Waynes World 2 (1993)
We're Back! A Dinosaur's Story (1993)
We're the Millers (2013)
Weird Science (1985)
Westworld - TV SHOW
Who Framed Roger Rabbit (1988)
Without a Paddle Nature's Calling (2004)
The Wolverine (2013) 
X
 
Y
Young Guns (1988)
Young Guns II (1990)
Yu Yu Hakusho - TV SHOW 
Z
Zack Snyder's Justice League (2021)
Zombieland (2009)
Zoolander (2001)
Zootopia (2016)
"""

SECTION_HEADERS = {
    "0-A",
    "A","B","C","D","E","F","G","H","I","J","K",
    "L","M","N","O","P","Q","R","S","T","U","V",
    "W","X","Y","Z"
}

def parse_default_media():
    movies: list[str] = []
    shows: list[str] = []

    for raw_line in RAW_MEDIA_LIST.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in SECTION_HEADERS:
            continue

        if " - TV SHOW" in line:
            title = line.replace(" - TV SHOW", "").strip()
            if title:
                shows.append(title)
        else:
            movies.append(line)

    return movies, shows

DEFAULT_MOVIES, DEFAULT_SHOWS = parse_default_media()


# ────────────────────── BIRTHDAY STORAGE ──────────────────────

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
    except:
        return {}
    content = msg.content.strip() or "{}"
    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}

async def _save_storage_message(data: dict):
    global storage_message_id
    channel = bot.get_channel(BIRTHDAY_STORAGE_CHANNEL_ID)
    if not channel or storage_message_id is None:
        return
    try:
        msg = await channel.fetch_message(storage_message_id)
    except:
        return
    text = json.dumps(data, indent=2)
    if len(text) > 1900:
        text = text[:1900]
    await msg.edit(content=text)


# ────────────────────── MEDIA (MOVIES / TV SHOWS) LISTS ──────────────────────

async def _load_titles_from_channel(channel_id: int) -> list[str]:
    """Read all non-empty messages from a channel and treat each as a title."""
    ch = bot.get_channel(channel_id)
    if not isinstance(ch, discord.TextChannel):
        print(f"[Media] Channel {channel_id} not found or not a text channel.")
        return []

    titles: list[str] = []
    try:
        async for msg in ch.history(limit=None, oldest_first=True):
            content = (msg.content or "").strip()
            if content:
                titles.append(content)
    except discord.Forbidden:
        print(f"[Media] No permission to read history in channel {channel_id}.")
    return titles


async def initialize_media_lists():
    """Load movies and TV shows from their storage channels into memory.
       If a storage channel is empty, seed it from DEFAULT_MOVIES / DEFAULT_SHOWS.
    """
    global movie_titles, tv_titles

    # Movies
    if MOVIE_STORAGE_CHANNEL_ID != 0:
        movie_titles = await _load_titles_from_channel(MOVIE_STORAGE_CHANNEL_ID)
        ch = bot.get_channel(MOVIE_STORAGE_CHANNEL_ID)
        if not movie_titles and isinstance(ch, discord.TextChannel):
            print("[Media] Movie storage empty, seeding from default list.")
            for title in DEFAULT_MOVIES:
                await ch.send(title)
            movie_titles = list(DEFAULT_MOVIES)
        print(f"[Media] Movies loaded: {len(movie_titles)}")
    else:
        print("[Media] MOVIE_STORAGE_CHANNEL_ID is 0 (movies disabled).")

    # TV shows
    if TV_STORAGE_CHANNEL_ID != 0:
        tv_titles = await _load_titles_from_channel(TV_STORAGE_CHANNEL_ID)
        ch = bot.get_channel(TV_STORAGE_CHANNEL_ID)
        if not tv_titles and isinstance(ch, discord.TextChannel):
            print("[Media] TV storage empty, seeding from default list.")
            for title in DEFAULT_SHOWS:
                await ch.send(title)
            tv_titles = list(DEFAULT_SHOWS)
        print(f"[Media] TV shows loaded: {len(tv_titles)}")
    else:
        print("[Media] TV_STORAGE_CHANNEL_ID is 0 (shows disabled).")


# ────────────────────── BIRTHDAY HELPERS ──────────────────────

def normalize_date(date_str: str):
    try:
        dt = datetime.strptime(date_str, "%m-%d")
        return dt.strftime("%m-%d")
    except ValueError:
        return None

async def set_birthday(guild_id: int, user_id: int, mm_dd: str):
    data = await _load_storage_message()
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    data[gid][str(user_id)] = mm_dd
    await _save_storage_message(data)

async def get_guild_birthdays(guild_id: int):
    data = await _load_storage_message()
    return data.get(str(guild_id), {})

async def build_birthday_embed(guild: discord.Guild) -> discord.Embed:
    birthdays = await get_guild_birthdays(guild.id)
    embed = discord.Embed(title="Our Birthdays!", color=0x2e2f33)
    if not birthdays:
        embed.description = (
            "No birthdays have been set yet.\n\n"
            "Use </set:1440919374310408234> to share your birthday"
        )
        return embed
    sorted_items = sorted(birthdays.items(), key=lambda x: x[1])
    lines = []
    for user_id, mm_dd in sorted_items:
        member = guild.get_member(int(user_id))
        name = member.display_name if member else f"User {user_id}"
        lines.append(f"`{mm_dd}` — **{name}**")
    lines.append("")
    lines.append("Use </set:1440919374310408234> to share your birthday")
    embed.description = "\n".join(lines)
    return embed

async def update_birthday_list_message(guild: discord.Guild):
    channel = bot.get_channel(BIRTHDAY_LIST_CHANNEL_ID)
    if not channel:
        print("Birthday list channel not found.")
        return
    try:
        msg = await channel.fetch_message(BIRTHDAY_LIST_MESSAGE_ID)
    except:
        print("Birthday list message not found.")
        return
    embed = await build_birthday_embed(guild)
    try:
        allowed = discord.AllowedMentions(users=True)
        await msg.edit(embed=embed, allowed_mentions=allowed)
        print("Birthday list updated.")
    except Exception as e:
        print("Failed to update list:", e)


# ────────────────────── SLASH COMMANDS ──────────────────────

@bot.slash_command(name="set", description="Set your birthday (MM-DD)")
async def set_birthday_self(ctx, date: discord.Option(str, "Format: MM-DD", required=True)):
    mm_dd = normalize_date(date)
    if not mm_dd:
        return await ctx.respond("Invalid date. Use MM-DD.", ephemeral=True)
    await set_birthday(ctx.guild.id, ctx.author.id, mm_dd)
    await update_birthday_list_message(ctx.guild)
    await ctx.respond(f"Your birthday has been set to `{mm_dd}`.", ephemeral=True)

@bot.slash_command(name="set_for", description="Set a birthday for another member (MM-DD)")
async def set_birthday_for(ctx,
    member: discord.Option(discord.Member, "Member", required=True),
    date: discord.Option(str, "Format: MM-DD", required=True),
):
    if not ctx.author.guild_permissions.administrator and ctx.guild.owner_id != ctx.author.id:
        return await ctx.respond("You need Administrator.", ephemeral=True)
    mm_dd = normalize_date(date)
    if not mm_dd:
        return await ctx.respond("Invalid date. Use MM-DD.", ephemeral=True)
    await set_birthday(ctx.guild.id, member.id, mm_dd)
    await update_birthday_list_message(ctx.guild)
    await ctx.respond(f"Birthday set for {member.mention} → `{mm_dd}`.", ephemeral=True)

@bot.slash_command(name="birthdays", description="Show all server birthdays")
async def birthdays_cmd(ctx):
    embed = await build_birthday_embed(ctx.guild)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="say", description="Make the bot say something in this channel")
async def say(ctx, message: discord.Option(str, "Message", required=True)):
    if not ctx.author.guild_permissions.administrator and ctx.guild.owner_id != ctx.author.id:
        return await ctx.respond("You need Administrator.", ephemeral=True)
    await ctx.channel.send(message)
    await ctx.respond("Sent!", ephemeral=True)

@bot.slash_command(name="remove_for", description="Remove a birthday for another member")
async def remove_birthday_for(ctx, member: discord.Option(discord.Member, "Member to remove birthday for", required=True)):
    if not ctx.author.guild_permissions.administrator and ctx.guild.owner_id != ctx.author.id:
        return await ctx.respond("You need Administrator.", ephemeral=True)
    data = await _load_storage_message()
    gid = str(ctx.guild.id)
    uid = str(member.id)
    if gid not in data or uid not in data[gid]:
        return await ctx.respond("That member has no birthday set.", ephemeral=True)
    del data[gid][uid]
    await _save_storage_message(data)
    await update_birthday_list_message(ctx.guild)
    await ctx.respond(f"Removed birthday for {member.mention}.", ephemeral=True)

@bot.slash_command(name="request", description="Request a movie or show for others to vote on")
async def request_cmd(ctx, title: discord.Option(str, "Movie or show title", required=True)):
    if MOVIE_REQUESTS_CHANNEL_ID == 0:
        return await ctx.respond("Movie requests channel is not configured.", ephemeral=True)

    channel = bot.get_channel(MOVIE_REQUESTS_CHANNEL_ID)
    if not channel:
        return await ctx.respond("Configured movie requests channel not found.", ephemeral=True)

    embed = discord.Embed(
        title=title,
        description=(
            f"Requested by {ctx.author.mention}\n\n"
            "**[REQUEST A TITLE](https://discord.com/channels/1205041211610501120/1440989357535395911/1440992347709243402)**"
        ),
        color=0x2e2f33,
    )

    msg = await channel.send(embed=embed)

    try:
        await msg.add_reaction("✅")
        await msg.add_reaction("🚫")
    except:
        pass

    await ctx.respond("Your request has been posted for voting.", ephemeral=True)


# ────────────────────── MEDIA COMMANDS ──────────────────────

@bot.slash_command(
    name="media_list",
    description="List stored movies or TV shows (ephemeral)"
)
async def media_list(
    ctx: discord.ApplicationContext,
    category: discord.Option(str, "Which list?", choices=["movies", "shows"], required=True),
):
    items = movie_titles if category == "movies" else tv_titles

    if not items:
        return await ctx.respond(f"No {category} stored.", ephemeral=True)

    lines = [f"{i+1}. {title}" for i, title in enumerate(items)]

    chunks = []
    current = []
    length = 0

    for line in lines:
        if length + len(line) + 1 > 1900:
            chunks.append("\n".join(current))
            current = [line]
            length = len(line) + 1
        else:
            current.append(line)
            length += len(line) + 1

    if current:
        chunks.append("\n".join(current))

    await ctx.respond(f"```\n{chunks[0]}\n```", ephemeral=True)

    for chunk in chunks[1:]:
        await ctx.followup.send(f"```\n{chunk}\n```", ephemeral=True)


@bot.slash_command(
    name="media_random",
    description="Pick a random movie or TV show from the stored lists"
)
async def media_random(
    ctx: discord.ApplicationContext,
    category: discord.Option(str, "Which list?", choices=["movies", "shows"], required=True),
):
    items = movie_titles if category == "movies" else tv_titles

    if not items:
        return await ctx.respond(f"No {category} stored yet.", ephemeral=True)

    choice = random.choice(items)
    await ctx.respond(f"🎲 Random {category[:-1]}: **{choice}**")


@bot.slash_command(
    name="media_add",
    description="Add a new movie or TV show to the stored lists"
)
async def media_add(
    ctx: discord.ApplicationContext,
    category: discord.Option(str, "Which list?", choices=["movies", "shows"], required=True),
    title: discord.Option(str, "Exact title to add", required=True),
):
    # Admin / owner only
    if not ctx.author.guild_permissions.administrator and ctx.guild.owner_id != ctx.author.id:
        return await ctx.respond("You need Administrator.", ephemeral=True)

    title = title.strip()
    if not title:
        return await ctx.respond("Title cannot be empty.", ephemeral=True)

    global movie_titles, tv_titles

    if category == "movies":
        if MOVIE_STORAGE_CHANNEL_ID == 0:
            return await ctx.respond("Movie storage channel is not configured.", ephemeral=True)
        if title in movie_titles:
            return await ctx.respond("That movie is already in the list.", ephemeral=True)

        ch = bot.get_channel(MOVIE_STORAGE_CHANNEL_ID)
        if not ch:
            return await ctx.respond("Movie storage channel not found.", ephemeral=True)

        await ch.send(title)
        movie_titles.append(title)
        await ctx.respond(f"Added **{title}** to movies.", ephemeral=True)

    else:  # shows
        if TV_STORAGE_CHANNEL_ID == 0:
            return await ctx.respond("TV storage channel is not configured.", ephemeral=True)
        if title in tv_titles:
            return await ctx.respond("That show is already in the list.", ephemeral=True)

        ch = bot.get_channel(TV_STORAGE_CHANNEL_ID)
        if not ch:
            return await ctx.respond("TV storage channel not found.", ephemeral=True)

        await ch.send(title)
        tv_titles.append(title)
        await ctx.respond(f"Added **{title}** to TV shows.", ephemeral=True)


# ────────────────────── EVENTS ──────────────────────

@bot.event
async def on_ready():
    print(f"{bot.user} is online (birthday bot).")
    await initialize_storage_message()
    await initialize_media_lists()   # ← load / seed movies & shows
    bot.loop.create_task(birthday_checker())

@bot.event
async def on_member_join(member):
    try:
        await member.send(
            """Hey, welcome to the server. Feel free to add your birthday in the channel below so we can all celebrate.

https://discord.com/channels/1205041211610501120/1440989357535395911/1440989655515271248"""
        )
    except:
        pass

async def birthday_checker():
    await bot.wait_until_ready()
    print("Birthday checker started.")
    while not bot.is_closed():
        today_mm_dd = datetime.utcnow().strftime("%m-%d")
        all_data = await _load_storage_message()
        for guild in bot.guilds:
            role = guild.get_role(BIRTHDAY_ROLE_ID)
            if not role:
                continue
            birthdays = all_data.get(str(guild.id), {})
            for member in guild.members:
                bday = birthdays.get(str(member.id))
                if bday == today_mm_dd:
                    if role not in member.roles:
                        try:
                            await member.add_roles(role, reason="Birthday")
                        except:
                            pass
                else:
                    if role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Birthday ended")
                        except:
                            pass
        await asyncio.sleep(3600)

bot.run(os.getenv("TOKEN"))
