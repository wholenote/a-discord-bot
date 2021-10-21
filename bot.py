import discord
import os
import requests
import random
import traceback
from dotenv import load_dotenv
from textblob import TextBlob
from discord.ext import commands
from instalooter.looters import PostLooter, ProfileLooter

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
    if any(s in ctx.content for s in os.getenv('BADWORDS').split(',')) or TextBlob(ctx.content).sentiment.polarity < 0:
        # reply = random.choice(['bro wtf!', str(requests.get('https://evilinsult.com/generate_insult.php?lang=en&type=text').text)])
        reply = str(requests.get('https://evilinsult.com/generate_insult.php?lang=en&type=text').text)
        await ctx.channel.send(reply)
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
    '''Pong! Get the bot's response time'''
    em = discord.Embed(color=discord.Color.green())
    em.title = "Pong!"
    em.description = f'{bot.latency * 1000} ms'
    await ctx.send(embed=em)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def monke(ctx):
    # TODO: pull posts from r/monke, ig daily.monkey.posts, also need to account for videos
    looter = ProfileLooter('a_p_e_k_i_n_g')
    posts = []
    for media in looter.medias():
        posts.append(media)
    post = random.randint(0, len(posts))
    url_code = posts[post]['shortcode']
    post_id = posts[post]['id']
    PostLooter(url_code).download('~/a-discord-bot', media_count=1)

    await ctx.channel.send(file=discord.File(post_id + '.jpg'))

    os.remove(post_id + '.jpg')
    return

@bot.command()
@commands.cooldown(2, 5, commands.BucketType.user)
async def austin(ctx):
    '''Get an Austin joke'''
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
    r = requests.get('https://v2.jokeapi.dev/joke/Dark')
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

# change nickname command
# noke

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))