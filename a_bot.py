import discord
import speech_recognition as sr
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient

import pyaudio

client = discord.Client()

@client.event
async def on_ready():
    print('Ready to listen.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('#start'):
        client.connect()
        while client.is_connected():
            await client.say('connected')
            if message.content.startswith('#stop'):
                return
            
    

bot.run('token here')
