import discord
import os
import requests
import random
import traceback
import time
import asyncio
import random
import re
import youtube_dl
from dotenv import load_dotenv
from textblob import TextBlob
from discord.ext import commands
from datetime import datetime
from discord_components import DiscordComponents, Button, Interaction
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from mysql.connector import connect, Error 

load_dotenv()

nltk.download('vader_lexicon')

try:
    connection = connect(
        host='localhost',
        user='monkebot',
        password=os.getenv('MYSQL_PW'),
        database='guild')
except Error as e:
    print(e)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='>', description='', intents=intents)
DiscordComponents(bot)

wordle_game_state = False
scramble_game_state = False

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def process_social_score(ctx):
    global connection

    msg = re.sub(r'https?://\S+', '', ctx.content)
    msg = re.sub(r'<((@!?\d+)|(:.+?:\d+))>', '', msg)
    blob = TextBlob(msg)
    sia = SentimentIntensityAnalyzer()
    msg_score = (blob.sentiment.polarity * 0.15 + sia.polarity_scores(msg)['compound']) * 1000
    
    # print(f'"{msg}" message social credit rating: {msg_score}, userid: {ctx.author.id}')

    if msg_score != 0:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT user_id FROM users WHERE user_id={ctx.author.id}')
            if cursor.fetchall():
                # fetch current score
                cursor.execute(f'SELECT social_score FROM users WHERE user_id={ctx.author.id}')
                result = cursor.fetchall()
                cur_score = result[0][0]
                cursor.execute(f'UPDATE users SET social_score={cur_score + msg_score} WHERE user_id={ctx.author.id}')
                connection.commit()
            else:
                cursor.execute(f'INSERT INTO users (user_id, social_score) VALUES ({ctx.author.id}, {msg_score})')
                connection.commit()

@bot.event
async def on_ready():
    print(f'Logged in as:\nUsername: {bot.user.name}\nID: {bot.user.id}')

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return
        
    bots_role = discord.utils.find(lambda r: r.name == 'Bots', ctx.guild.roles)
    if bots_role not in ctx.author.roles and ctx.channel.id == 272232225112850433:
        process_social_score(ctx)

    await bot.process_commands(ctx)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MissingRequiredArgument):
        pass
    elif isinstance(error, commands.NotOwner):
        pass
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.channel.send("You can't use that command in a private message.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.channel.send("You don't have the required permissions to do that.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(error)
    else:
        print(''.join(traceback.format_exception(type(error), error, error.__traceback__)))

@bot.command(hidden=True)
async def test(ctx):
    '''Test Command.'''
    em = discord.Embed(color=discord.Color.green())
    em.title = 'Test Success!'
    await ctx.send(embed=em)
    return

@bot.command()
async def ping(ctx):
    '''Pong! Get the bot's response time.'''
    em = discord.Embed(color=discord.Color.green())
    em.title = "Pong!"
    em.description = f'{bot.latency * 1000} ms'
    await ctx.send(embed=em)

@bot.command()
async def play(ctx, url):
    """Plays from a url (almost anything youtube_dl supports)"""

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f'Now playing: {player.title}')

@bot.command()
async def stop(ctx):
    """Stops and disconnects the bot from voice"""

    await ctx.voice_client.disconnect()

@play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

@bot.command()
async def scredit(ctx, option=None):
    '''Get social credit. Example Usage: >scredit or >scredit lb'''
    global connection

    if option == None:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT user_id, social_score FROM users WHERE user_id={ctx.author.id}')
            result = cursor.fetchall()[0]
            em = discord.Embed(color=discord.Color.blue())
            em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            em.add_field(name='Social Credit Score:', value=result[1], inline=True)
            await ctx.send(embed=em)
    elif option == 'lb':
        with connection.cursor() as cursor:
            cursor.execute('SELECT user_id, social_score FROM users ORDER BY social_score DESC')
            result = cursor.fetchall()
            em = discord.Embed(color=discord.Color.blue())
            em.set_author(name='Social Credit Leaderboard')
            description = ''
            for i in range(len(result)):
                user = await bot.fetch_user(result[i][0])
                line = f'**{i+1}.**  {user.name} • {result[i][1]}'
                description += line + '\n'
            em.description = description
            await ctx.send(embed=em)

    return

@bot.command()
@commands.cooldown(2, 5, commands.BucketType.user)
async def austin(ctx):
    '''Get an Austin joke.'''
    r = requests.get('https://v2.jokeapi.dev/joke/Pun')
    if r.json()['type'] == 'twopart':
        em = discord.Embed(color=discord.Color.green())
        em.title = "An Austin Joke"
        em.description = f'{r.json()["setup"]}\n\n||{r.json()["delivery"]}||'
        await ctx.send(embed=em)
    else:
        em = discord.Embed(color=discord.Color.green())
        em.title = "An Austin Joke"
        em.description = f'{r.json()["joke"]}'
        await ctx.send(embed=em)
    return

@bot.command()
@commands.cooldown(2, 5, commands.BucketType.user)
async def joke(ctx):
    '''Random Joke.'''
    r = requests.get('https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist')
    if r.json()['type'] == 'twopart':
        em = discord.Embed(color=discord.Color.green())
        em.title = "Joke"
        em.description = f'{r.json()["setup"]}\n\n||{r.json()["delivery"]}||'
        await ctx.send(embed=em)
    else:
        em = discord.Embed(color=discord.Color.green())
        em.title = "Joke"
        em.description = f'{r.json()["joke"]}'
        await ctx.send(embed=em)
    return

@bot.command()
@commands.cooldown(1, 1, commands.BucketType.guild)
async def wordle(ctx, option=None):
    '''Play wordle with a random word.'''
    
    global wordle_game_state
    global connection

    if ctx.channel.id != 277973665230880770:
        return
    if option == 'lb':
        with connection.cursor() as cursor:
            cursor.execute('SELECT user_id, wordle_score FROM users ORDER BY wordle_score DESC')
            result = cursor.fetchall()
            em = discord.Embed(color=discord.Color.blue())
            em.set_author(name='Wordle Leaderboard')
            description = ''
            for i in range(len(result)):
                user = await bot.fetch_user(result[i][0])
                line = f'**{i+1}.**  {user.name} • {result[i][1]}'
                description += line + '\n'
            em.description = description
            await ctx.send(embed=em)
        return
    if wordle_game_state:
        await ctx.send("A wordle game is in progress. Try again later.")
        return

    wordle_game_state = True

    tiles_msg = await ctx.send("Word picked. Start guessing...")
    check = lambda m: m.channel == ctx.channel and len(m.content) == 5

    words_file = open("wordle_words.txt", "r")
    word_list = words_file.read().split("\n")
    words_file.close()
    word_size = 5
    seed = int(time.mktime(datetime.now().timetuple()))
    random.seed(seed)
    word = random.choice(word_list)
    cur_tiles = ""
    guess_count = 0

    while True:
        try:
            guess = await bot.wait_for("message", check=check, timeout=120)
        except asyncio.TimeoutError:
            await ctx.send(f"Wordle game ended, timed out. The word was ||{word}||.")
            wordle_game_state = False
            return

        r = requests.get('https://v1.wordle.k2bd.dev/word/{}'.format(word), params={'guess': (guess.content).lower()})

        if r.status_code == 200 and (guess.content).lower() in word_list:
            guess_count += 1
            for i in range(word_size):
                if r.json()[i]['result'] == "correct":
                    cur_tiles += ":green_square:"
                elif r.json()[i]['result'] == "present":
                    cur_tiles += ":yellow_square:"
                elif r.json()[i]['result'] == "absent":
                    cur_tiles += ":black_large_square:"
            cur_tiles = cur_tiles + "   " + (guess.content).upper()
            cur_tiles += "\n"

            # keep wordle game board on screen
            if guess_count > 6:
                tiles_msg = await ctx.send(content=cur_tiles)
                guess_count = 0
            else:
                await tiles_msg.edit(content=cur_tiles)

            if (guess.content).lower() == word:
                await ctx.send("<@{}> wins! **+100 wordle pts**".format(guess.author.id))
                wordle_game_state = False
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT user_id FROM users WHERE user_id={ctx.author.id}')
                    if cursor.fetchall():
                        # fetch current score
                        cursor.execute(f'SELECT wordle_score FROM users WHERE user_id={ctx.author.id}')
                        result = cursor.fetchall()
                        cur_score = result[0][0]
                        cursor.execute(f'UPDATE users SET wordle_score={cur_score + 100} WHERE user_id={ctx.author.id}')
                        connection.commit()
                    else:
                        cursor.execute(f'INSERT INTO users (user_id, wordle_score) VALUES ({ctx.author.id}, {100})')
                        connection.commit()
                return
        elif r.status_code != 200:
            print(r.text)

@bot.command()
@commands.cooldown(1, 1, commands.BucketType.guild)
async def scramble(ctx, option=None):
    '''Play scrambled with a random 5 letter word.'''

    global scramble_game_state
    global connection

    if ctx.channel.id != 277973665230880770:
        return
    if option == 'lb':
        with connection.cursor() as cursor:
            cursor.execute('SELECT user_id, scramble_score FROM users ORDER BY scramble_score DESC')
            result = cursor.fetchall()
            em = discord.Embed(color=discord.Color.blue())
            em.set_author(name='Scramble Leaderboard')
            description = ''
            for i in range(len(result)):
                user = await bot.fetch_user(result[i][0])
                line = f'**{i+1}.**  {user.name} • {result[i][1]}'
                description += line + '\n'
            em.description = description
            await ctx.send(embed=em)
        return
    if scramble_game_state:
        await ctx.send("A wordle game is in progress. Try again later.")
        return
    
    scramble_game_state = True

    words_file = open("wordle_words.txt", "r")
    word_list = words_file.read().split("\n")
    words_file.close()

    seed = int(time.mktime(datetime.now().timetuple()))
    random.seed(seed)
    word = random.choice(word_list)

    tmp = list(word)
    random.shuffle(tmp)
    scrambled_word = ''.join(tmp)

    em = discord.Embed(color=discord.Color.green())
    em.title = "Guess the Scrambled Word"
    em.description = scrambled_word.upper()
    await ctx.send(embed=em)

    check = lambda m: m.channel == ctx.channel and len(m.content) == 5

    while True:
        try:
            guess = await bot.wait_for("message", check=check, timeout=120)
        except asyncio.TimeoutError:
            await ctx.send(f"Scramble game ended, timed out. The word was ||{word}||.")
            scramble_game_state = False
            return
        
        if (guess.content).lower() == word:
            await ctx.send("<@{}> wins! **+100 scramble pts**".format(guess.author.id))
            scramble_game_state = False
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT user_id FROM users WHERE user_id={ctx.author.id}')
                if cursor.fetchall():
                    # fetch current score
                    cursor.execute(f'SELECT scramble_score FROM users WHERE user_id={ctx.author.id}')
                    result = cursor.fetchall()
                    cur_score = result[0][0]
                    cursor.execute(f'UPDATE users SET scramble_score={cur_score + 100} WHERE user_id={ctx.author.id}')
                    connection.commit()
                else:
                    cursor.execute(f'INSERT INTO users (user_id, scramble_score) VALUES ({ctx.author.id}, {100})')
                    connection.commit()
            return

@bot.command()
@commands.cooldown(5, 5, commands.BucketType.guild)
async def udefine(ctx, word: str):
    '''Lookup Urban Dictionary definition.'''
    url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

    querystring = {"term": word}

    headers = {
        "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com",
        "X-RapidAPI-Key": os.getenv('URBAND_TOKEN')
    }

    r = requests.request("GET", url, headers=headers, params=querystring)

    index = 0
    em = discord.Embed(color=discord.Color.green())
    em.title = "Urban Dictionary Definition"
    em.description = f"**{word}**:\n\n{r.json()['list'][0]['definition'].replace('[', '').replace(']','')}\n\n*{r.json()['list'][0]['example'].replace('[', '').replace(']','')}*"

    async def next_callback(interaction: Interaction):
        nonlocal index
        if index == len(r.json()['list']) - 1:
            index = 0
        else:
            index += 1
        
        em.description = f"**{word}**:\n\n{r.json()['list'][index]['definition'].replace('[', '').replace(']','')}\n\n*{r.json()['list'][index]['example'].replace('[', '').replace(']','')}*"
        await interaction.edit_origin(embed=em)
        
    await ctx.send(embed=em, components=[bot.components_manager.add_callback(Button(label="Penis", custom_id="next"), next_callback)])

bot.run(os.getenv('DISCORD_TOKEN'))