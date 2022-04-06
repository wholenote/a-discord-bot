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

intents = discord.Intents.default()
intents.members = True

bot =  commands.Bot(command_prefix='>', description='', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as:\nUsername: {bot.user.name}\nID: {bot.user.id}')

@bot.event
async def on_message(ctx):
    if ctx.author == bot.user:
        return
    # if TextBlob(ctx.content).sentiment.polarity < 0:
        
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
        await ctx.channel.send("You can't use that command in a private message")
    elif isinstance(error, commands.CheckFailure):
        await ctx.channel.send("You don't have the required permissions to do that")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(error)
    else:
        print(''.join(traceback.format_exception(type(error), error, error.__traceback__)))

@bot.command()
async def test(ctx):
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
@commands.cooldown(1, 20, commands.BucketType.guild)
async def wordle(ctx):
    '''Play wordle with a random word.'''
    
    worlde_game_state = False

    if ctx.channel.id != 277973665230880770:
        return
    if worlde_game_state:
        await ctx.send("A wordle game is in progress. Try again later.")
        return

    worlde_game_state = True

    tiles_msg = await ctx.send("Word picked. Start guessing...")
    check = lambda m: m.channel == ctx.channel and len(m.content) == 5

    words_file = open("actual_wordle_words.txt", "r")
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
            worlde_game_state = False
            return

        # r = requests.get('https://v1.wordle.k2bd.dev/random', params={'guess': guess.content, 'size': word_size, 'seed': seed})
        r = requests.get('https://v1.wordle.k2bd.dev/word/{}'.format(word), params={'guess': (guess.content).lower()})
        # word_check = requests.get('https://api.dictionaryapi.dev/api/v2/entries/en/{}'.format(guess.content))

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

            # # correct guess logic
            # if cur_tiles.split("\n")[-2] == ":green_square:"*word_size:
            #     await ctx.send("{} wins!".format(guess.author.name))
            #     worlde_game_state = False
            #     channel = bot.get_channel(837436992232488961)
            #     await channel.send("%add-money bank <@{}> 1000".format(ctx.author.id))
            #     return

            if (guess.content).lower() == word:
                await ctx.send("<@{}> wins!".format(guess.author.id))
                worlde_game_state = False
                channel = bot.get_channel(837436992232488961)
                await channel.send("%add-money bank <@{}> 1000".format(guess.author.id))
                return
        else:
            print(r.text)

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.guild)
async def scramble(ctx):
    '''Play scrambled with a random 5 letter word.'''

    if ctx.channel.id != 277973665230880770:
        return
    
    words_file = open("actual_wordle_words.txt", "r")
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
            return
        
        if (guess.content).lower() == word:
            await ctx.send("<@{}> wins!".format(guess.author.id))
            return

worlde_game_state = False

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))