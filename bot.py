import os, json, random, time
import discord
from discord.ext import commands

intents = discord.Intents(messages=True, guilds=True, voice_states=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)

#----------#
# COMMANDS #
#----------#

# Awake check
awake_check_messages = []
with open('messages.txt') as messages:
    awake_check_messages = [line.rstrip() for line in messages.readlines()]

message_odds = 0.7
@bot.command(name='awake-check', help="Disconnects all users from the given voice channel")
async def awake_check(ctx, channel_name):
    try:
        prefix = get_prefix()
        for member in discord.utils.get(ctx.guild.voice_channels, name=channel_name).members:
            # Disconnect the given user
            await member.move_to(None)
            await send_message(prefix, ctx.author.nick, member)
    except Exception as e:
        print(e)

# Sleep
@bot.command(name='sleep', help="Forcibly sleeps the given user by nickname")
async def sleep(ctx, name):
    try:
        member = discord.utils.get(ctx.guild.members, nick=name)
        if  member.voice.channel is not None:
            await member.move_to(None)
            await send_message(get_prefix(), ctx.author.nick, member)
    except Exception as e:
        print(e)

# HELPER FUNCTIONS for awake_check and sleep

# Sends a message to the user containing the given previx and suffix and either:
#   - an additional message from messages.txt
#   - an image from ./images
# randomly chosen
async def send_message(prefix, suffix, member):
    try:
        if random.randrange(0, 1) <= message_odds:
            # Send a message
            await member.send(content=prefix + random.choice(awake_check_messages) + " - " + suffix)
        else:
            # Send a file
            await member.send(content=prefix + suffix,
                                file=discord.File('./images/' + random.choice(os.listdir('./images'))))
    except Exception as e:
        print("message")

# Returns the current local time in H:M:S format followed by a :
def get_prefix():
    return time.strftime("%H:%M:%S", time.localtime()) + ": "

# Shun
@bot.command(name='shun', help="Shuns the given user by nickname")
async def shun(ctx, name):
    try:
        # Moves the user to a "timeout" channel
        (await discord.utils.get(ctx.guild.members, nick=name)
                      .move_to(discord.utils.get(ctx.guild.channels, name='timeout')))
    except Exception as e:
        print(e)

#-----------------------#
# SOCIAL CREDIT RELATED #
#-----------------------#

# Dictionaries to be loaded from files
user_to_credit = {}
with open('database.json') as database:
    user_to_credit = json.load(database)

# Loads external files
@bot.event
async def on_ready():
    print("Bot finished loading external files!")

# Saves database with updated scores
@bot.event
async def close():
    with open('database.json', 'w') as db:
        json.dump(user_to_credit, db)

auth = json.load(open('auth.json'))
TOKEN = auth['token']
bot.run(TOKEN)