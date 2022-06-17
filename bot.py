import os, json, random, time
import discord
from discord.ext import commands

auth = json.load(open('auth.json'))
intents = discord.Intents(messages=True, guilds=True, voice_states=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)

# Awake check command
awake_check_messages = []
with open('messages.txt') as messages:
    lines = messages.readlines()
    awake_check_messages = [line.rstrip() for line in lines]
message_odds = 0.8
@bot.command(name='awake-check', help=("Disconnects all users from the given voice channel " +
                                       "and sends them an appropriate message"))
async def awake_check(ctx, channel_name):
    try:
        prefix = time.strftime("%H:%M:%S", time.localtime()) + ": "
        suffix = ctx.author.nick
        for member in discord.utils.get(ctx.guild.voice_channels, name=channel_name).members:
            # Disconnect the given user
            await member.move_to(None)
            
            if random.randrange(0, 1) <= message_odds:
                # Send a message
                await member.send(content=prefix + random.choice(awake_check_messages) + " - " + suffix)
            else:
                # Send a file
                await member.send(content=prefix + suffix,
                                  file=discord.File('./images/' + random.choice(os.listdir('./images'))))
    except Exception as e:
        print(e)

# Shun command
@bot.command(name='shun', help="Shuns the given user")
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

user_to_credit = {}
penalties = {}

# Loads from file
@bot.event
async def on_ready():
    with open('database.json') as db:
        user_to_credit = json.load(db)
    with open('penalties.json') as db:
        penalties = json.load(db)
    print("Bot finished loading!")

# Saves to file
@bot.event
async def close():
    with open('database.json', 'w') as db:
        json.dump(user_to_credit, db)

# Game update event
@bot.event
async def on_member_update(prev, cur):
    if cur.activity.name in penalties:
        if cur.id not in user_to_credit:
            user_to_credit[cur.id] = 0
        
        user_to_credit[cur.id] += penalties[cur.activity.name]

TOKEN = auth['token']
bot.run(TOKEN)