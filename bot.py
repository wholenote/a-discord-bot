import discord
import os
from dotenv import load_dotenv
from textblob import TextBlob

async def test_func(message, args):
    await message.channel.send('test success!')
    return

cmd_list = ['test']

def parse_msg(msg):
    cmd = {}
    msg = msg[1:].strip().split(' ')
    if msg[0] in cmd_list:
        cmd['cmd'] = msg.pop(0)
        cmd['arguments'] = ' '.join(msg) # leave argument parsing to specific cmd function
        return cmd
    else:
        return None

async def exec_cmd(cmd, message):
    if cmd.get('cmd') == 'test':
        await test_func(message, cmd.get('arguments'))
    return

async def process_cmd(message):
    cmd = parse_msg(message.content)
    if cmd:
        await exec_cmd(cmd, message)
    return

if __name__ == '__main__':
    load_dotenv()
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f'Logged in as:\nUsername: {client.user.name}\nID: {client.user.id}')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if message.content.startswith('>'):
            await process_cmd(message)
        if any(s in message.content for s in os.getenv('BADWORDS').split(',')) or TextBlob(message.content).sentiment.polarity < 0:
            await message.channel.send('bro wtf')

    client.run(os.getenv('DISCORD_TOKEN'))
