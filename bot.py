import discord
import os
import requests
import random
import traceback
import time
import asyncio
import random
from dotenv import load_dotenv
from textblob import TextBlob
from discord.ext import commands
from datetime import datetime
from discord_components import DiscordComponents, Button, Interaction

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='>', description='', intents=intents)
DiscordComponents(bot)

wordle_game_state = False
scramble_game_state = False

@bot.event
async def on_ready():
    print(f'Logged in as:\nUsername: {bot.user.name}\nID: {bot.user.id}')

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return
        
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

@bot.command()
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
async def wordle(ctx):
    '''Play wordle with a random word.'''
    
    global wordle_game_state

    if ctx.channel.id != 277973665230880770:
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

        if r.status_code == 200 and guess.content in word_list:
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
                await ctx.send("<@{}> wins!".format(guess.author.id))
                wordle_game_state = False
                channel = bot.get_channel(837436992232488961)
                await channel.send("%add-money bank <@{}> 1000".format(guess.author.id))
                return
        elif r.status_code != 200:
            print(r.text)

@bot.command()
@commands.cooldown(1, 1, commands.BucketType.guild)
async def scramble(ctx):
    '''Play scrambled with a random 5 letter word.'''

    global scramble_game_state

    if ctx.channel.id != 277973665230880770:
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
            await ctx.send("<@{}> wins!".format(guess.author.id))
            scramble_game_state = False
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
        
    await ctx.send(embed=em, components=[bot.components_manager.add_callback(Button(label="Next", custom_id="next"), next_callback)])

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))