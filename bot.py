import os, json, random, time, datetime, re
from bayes import NaiveBayes
import discord
from discord.ext import commands

intents = discord.Intents(messages=True, guilds=True, voice_states=True, members=True)
bot = commands.Bot(command_prefix='*', intents=intents)

#-----------#
# CONSTANTS #
#-----------#

message_odds = 0.4      # Percentage odds of sending a message over a file
time_min = '20:00'      # Minimum time to flame people for good morning message
embed_max = 4096        # Maximum length of embed descriptions

db_file = 'database.json'   # File name for database
auth_file = 'auth.json'     # File name for auth
base_dir = './data'         # Base directory for naive bayes

#--------------------#
# Loading from files #
#--------------------#

# Text messages used for awake_check / sleep stored in messages.txt
awake_check_messages = []
with open('messages.txt') as messages:
    awake_check_messages = [line.rstrip() for line in messages.readlines()]

# User to cringe credit calculated over lifetime stored in database.json
user_to_credit = {}
with open('database.json') as database:
    user_to_credit = json.load(database)

# Word to its associated penalty stored in penalties.json
word_to_penalty = {}
with open('penalties.json') as penalties:
    word_to_penalty = json.load(penalties)

#----------#
# COMMANDS #
#----------#

# Awake check
@bot.command(name='awake-check', help="Disconnects all users from the given voice channel")
async def awake_check(ctx, channel_name):
    try:
        prefix = get_prefix()
        for member in discord.utils.get(ctx.guild.voice_channels, name=channel_name).members:
            await member.move_to(None)
            await send_message(prefix, member)
    except Exception as e:
        print(e)

# Sleep
@bot.command(name='sleep', help="Forcibly sleeps the given user by nickname")
async def sleep(ctx, name):
    try:
        member = discord.utils.get(ctx.guild.members, nick=name)
        if  member.voice.channel is not None:
            await member.move_to(None)
            await send_message(get_prefix(), member)
    except Exception as e:
        print(e)

#====================================================================#
# Helper functions for awake_check and sleep

# Sends a message to the user containing the given previx and suffix and either:
#   - an additional message from messages.txt
#   - an image from ./images
# randomly chosen
async def send_message(prefix, member):
    try:
        if random.randrange(0, 1) <= message_odds:
            # Send a message
            await member.send(content=prefix + random.choice(awake_check_messages))
        else:
            # Send a file
            await member.send(content=prefix,
                                file=discord.File('./images/' + random.choice(os.listdir('./images'))))
    except Exception as e:
        print("message")

# Returns the current local time in H:M:S format followed by a :
def get_prefix():
    return time.strftime("%H:%M:%S", time.localtime()) + ": "

#====================================================================#

# Shun
@bot.command(name='shun', help="Shuns the given user by nickname")
async def shun(ctx, name):
    try:
        # Moves the user to a "timeout" channel
        (await discord.utils.get(ctx.guild.members, nick=name)
                      .move_to(discord.utils.get(ctx.guild.channels, name='timeout')))
    except Exception as e:
        print(e)

# Search
@bot.command(name='search', help="Searches through previous messages given word/phrase and depth")
async def search(ctx, word, limit:int=10, author=None):
    try:
        messages = await ctx.channel.history(limit=limit).flatten()
        results = ["[" + msg.author.nick + ": " + str(msg.created_at.date()) + "](" + msg.jump_url + ")" 
                   for msg in messages if word in msg.content and
                                          not msg.author.bot and
                                          msg.jump_url is not None and
                                          msg.author.nick is not None]

        result_str = ("Nothing found :(" if not results[1::] 
                                         else "Results for \'" + word + "\' at limit " + str(limit) + ":\n" +
                                              "\n".join(results[1::]))
        embed = discord.Embed()
        embed.description = (result_str if len(result_str) <= embed_max else 
                             result_str[:result_str[:embed_max].rfind('\n')])
        await ctx.channel.send(embed=embed)
    except Exception as e:
        print(e)

@bot.command(name='export', help="Exports all messages in the channel to a txt file up to a specific depth")
async def export(ctx, limit:int=200):
    try:
        with open('log.txt', 'w') as log:
            messages = await ctx.channel.history(limit=limit).flatten()
            results = {format_line(msg.content) for msg in messages if not msg.author.bot and
                                                         not msg.content.startswith('!') and
                                                         not msg.content.startswith('*')}
            log.write("\n".join(results))
            log.close()
            
            await ctx.channel.send(content=get_prefix() + ctx.channel.name + " log",
                                   file=discord.File('log.txt'))
            os.remove('log.txt')
    except Exception as e:
        print(e)

# Removes all text between <> characters, fits everything to one line, and removes leading/trailing spaces
def format_line(line):
    return re.sub('<[^>]+>', '', line).replace("\n", " ").strip()

"""
Currently commented out to see what accumulates naturally

# Scores
@bot.command(name='scores', help="Prints out user's cringe-scores calculated from proprietary algorithms")
async def score(ctx):
    try:
        for user, credit in user_to_credit.items():
            member = discord.utils.get(ctx.guild.members, id=user)
            if member is not None:
                await ctx.channel.send(member.nick + ": " + str(credit))
    except Exception as e:
        print(e)
"""


#-----------------------#
# SOCIAL CREDIT RELATED #
#-----------------------#

nb = NaiveBayes()
nb.train(os.path.join(base_dir, "train", "cringe.txt"),
         os.path.join(base_dir, "train", "based.txt"))

def test_cringe(file):
    total = 0
    cringe = 0

    with open(file) as f:
        for line in f:
            formatted = format_line(line)
            total += 1
            if nb.predict(formatted):
                cringe += 1
                #print(formatted)
    return cringe / total

print("Cringe accuracy: " + str(test_cringe(os.path.join(base_dir, "test", "cringe.txt"))))
print("Based accuracy: " + str(1 - test_cringe(os.path.join(base_dir, "test", "based.txt"))))

# Saves database with updated scores
@bot.event
async def close():
    with open(db_file, "w") as db:
        json.dump(user_to_credit, db)

# General responses to messages sent as non-commands
@bot.event
async def on_message(message):
    lower = message.content.lower()

    # Flames users for saying "good morning" late at night
    if "good morning" in lower and time.strftime('%H:%M') > time_min:
        await message.channel.send("It's " + time.strftime('%H:%M') + "...")
    
    # Secretly tallies if a message is considered cringe or not
    formatted = format_line(message.content)
    if nb.predict(formatted):
        user_to_credit[str(message.author.id)] = user_to_credit.get(str(message.author.id), 0) + 1
    
    """
    # Secretly calculates based on penalties file
    for word, penalty in word_to_penalty.items():
        if word in lower:
            user_to_credit[str(message.author.id)] = user_to_credit.get(str(message.author.id), 0) + penalty
    """

    # Continue processing other commands
    await bot.process_commands(message)

# Prints out when the bot is up and running!
@bot.event
async def on_ready():
    print("Bot finished loading external files!")

auth = json.load(open(auth_file))
TOKEN = auth['token']
bot.run(TOKEN)