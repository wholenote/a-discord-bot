import discord
import speech_recognition as sr
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient

import pyaudio

bot = commands.Bot(command_prefix='#')

@bot.event
async def on_ready():
    print('Ready to steal your information.')

@bot.command()
async def start(ctx):
    '''
    Bot joins the channel you are in. Google Speech Recognition starts.
    '''
    author = ctx.message.author
    channel = author.voice_channel
    await bot.join_voice_channel(channel)



bot.run('token here')
