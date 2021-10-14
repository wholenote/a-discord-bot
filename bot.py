import discord

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

def exec_cmd(cmd, message):
    if cmd.get('cmd') == 'test':
        test_func(message, cmd.get('arguments'))
    return

def process_cmd(message):
    cmd = parse_msg(message.content)
    if cmd:
        exec_cmd(cmd, message)
    return

if __name__ == '__main__':
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f'Logged in as:\nUsername: {client.user.name}\nID: {client.user.id}.')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if message.content.startswith('>'):
            process_cmd(message)    

    client.run('token here')
