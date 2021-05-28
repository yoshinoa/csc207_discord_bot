import discord
from discord.ext import commands
import os
import pickle
from dotenv import load_dotenv
from typing import Dict
import pendulum
from user import User
from guild import Guild
from meetings import Meeting
import meetings
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone
import globals
from weekday import Day

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
client = commands.Bot(intents=intents, command_prefix='-')
REACTION_IDS, REVERSE_DICT, DAYS_OF_WEEK, all_guilds = globals.init()

def parse_timezone(timezone: str) -> str:
    '''
    Given a string, return the same string back if this str can be parsed
    as a timezone
    '''
    try:
        now = pendulum.now("EST")
        now.in_timezone(timezone)
        return timezone
    except InvalidTimezone:
        return ''


def format_date_dictionary(user: User, input_dict: Dict[str, Day]):
    string = f"Times are in **{user.timezone}**\n```"
    local_availability = user.localize_dictionary(input_dict)
    for day in local_availability:
        times = []
        for value in local_availability[day].times:
            if local_availability[day].times[value]:
                times.append(value)
        if times:
            string += day + ": "
            for value in times:
                string += str(value) + ":00, "
            string = string[:-2] + "\n"
    string += '```'
    return string

async def get_member(new_user, owo_client):
    for item in owo_client.guilds:
        test_item = await item.fetch_member(new_user.id)
        if test_item is not None:
            return test_item


async def onstart(client_item):
    if os.path.exists("session.pickle"):
        with open("session.pickle", 'rb') as pickle_file:
            pickle_data = pickle.load(pickle_file)
        global all_guilds
        all_guilds = pickle_data['initialized_guilds']
        meetings.globvar = pickle_data['globvar']


def write_file():
    writing_dict = {"initialized_guilds": all_guilds, 'globvar': meetings.globvar}
    with open("session.pickle", "wb") as pickle_file:
        pickle.dump(writing_dict, pickle_file)


async def initialize_server(guild: discord.guild):
    new_guild = Guild(guild.id)
    overwrites = {guild.default_role: discord.PermissionOverwrite(send_messages=False)}
    channel = await guild.create_text_channel('availability', overwrites=overwrites)
    await channel.send(f'In order to use commands react to the messages here!')
    message = await channel.send(f'**Select your timezone.** If your timezone isn\'t here use the command -timezone (your timezone)')
    for TZ in ['EST', 'PST', 'JST', 'CST', 'KST']:
        await message.add_reaction(REACTION_IDS[TZ])
    for days in DAYS_OF_WEEK:
        message = await channel.send(days[0])
        new_guild.add_message_id(message.id, days[0])
        for x in range(1, 21):
            await message.add_reaction(REACTION_IDS[x])
        message = await channel.send(days[1])
        new_guild.add_message_id(message.id, days[0])
        for x in range(21, 24):
            await message.add_reaction(REACTION_IDS[x])
        await message.add_reaction(REACTION_IDS[0])
    all_guilds[guild.id] = new_guild
    write_file()
    print(f"initialized guild {guild.name}")


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if client.user.id != payload.user_id:
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = client.get_user(payload.user_id)
        emoji = payload.emoji
        if str(emoji) not in REVERSE_DICT:
            await message.remove_reaction(emoji, user)
        elif 'Select your timezone.' in message.content:
            if payload.user_id in all_guilds[payload.guild_id].users:
                await message.remove_reaction(emoji, user)
            else:
                all_guilds[payload.guild_id].add_user(User(payload.user_id, REVERSE_DICT[str(emoji)]))
                write_file()
        else:
            if payload.user_id in all_guilds[payload.guild_id].users:
                local_user = all_guilds[payload.guild_id].users[payload.user_id]
                time_set = REVERSE_DICT[str(emoji)]
                day_set = all_guilds[payload.guild_id].get_day(payload.message_id)
                local_user.add_time(time_set, day_set)
                write_file()
            else:
                await message.remove_reaction(emoji, user)

async def remove_all_reactions(payload, user: discord.User):
    channel = client.get_channel(payload.channel_id)
    local_dict = all_guilds[payload.guild_id].users[user.id].true_dict()
    new_dict = {}
    for x in local_dict:
        for i in local_dict[x]:
            if i > 20:
                if all_guilds[payload.guild_id].weekday_message_ids[x][1] in new_dict:
                    new_dict[all_guilds[payload.guild_id].weekday_message_ids[x][1]].append(REACTION_IDS[i])
                else:
                    new_dict[all_guilds[payload.guild_id].weekday_message_ids[x][1]] = [REACTION_IDS[i]]
            else:
                if all_guilds[payload.guild_id].weekday_message_ids[x][0] in new_dict:
                    new_dict[all_guilds[payload.guild_id].weekday_message_ids[x][0]].append(REACTION_IDS[i])
                else:
                    new_dict[all_guilds[payload.guild_id].weekday_message_ids[x][0]] = [REACTION_IDS[i]]
    for item in new_dict:
        local_message = await channel.fetch_message(item)
        for item2 in new_dict[item]:
            await local_message.remove_reaction(item2, user)


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = client.get_user(payload.user_id)
    emoji = payload.emoji
    if str(emoji) in REVERSE_DICT:
        if 'Select your timezone.' in message.content:
            if payload.user_id in all_guilds[payload.guild_id].users and \
                    all_guilds[payload.guild_id].users[payload.user_id].\
                    timezone == REVERSE_DICT[str(emoji)]:
                await remove_all_reactions(payload, user)
                all_guilds[payload.guild_id].remove_user(payload.user_id)
                write_file()
        else:
            if payload.user_id in all_guilds[payload.guild_id].users:
                local_user = all_guilds[payload.guild_id].users[payload.user_id]
                time_set = REVERSE_DICT[str(emoji)]
                day_set = all_guilds[payload.guild_id].get_day(payload.message_id)
                local_user.remove_time(time_set, day_set)
                write_file()


@client.event
async def on_ready():
    await onstart(client)
    await client.change_presence(activity=discord.Activity(name='status', details="Type !commands to see a list of commands", ))
    for server in client.guilds:
        if server.id not in all_guilds:
            await initialize_server(server)
    print(f"{client.user} has connected to discord!")


@client.command(name='meeting',
                help="Usage: -meeting @user1 @user2 ex. -meeting @132ads",
                brief="Gives meeting times for this user and the tagged other users.")
async def meeting(context):
    message = context.message
    users_to_check = []
    userids = []
    try:
        message.mentions[0]
    except IndexError:
        await message.channel.send(f"Input did not contain another user, please @ them.")
    for user in message.mentions:
        if message.guild.id in all_guilds and user.id in all_guilds[message.guild.id].users:
            users_to_check.append(all_guilds[message.guild.id].users[user.id])
            userids.append(user.id)
        else:
            await message.channel.send(f"{user.name} hasn't set their schedule.")
    if userids:
        date_dict = all_guilds[message.guild.id].users[message.author.id].compare_with(users_to_check)
        all_guilds[message.guild.id].users[message.author.id].last_command = all_guilds[message.guild.id].users[message.author.id].localize_dictionary(date_dict), userids
        formatted_text = format_date_dictionary(all_guilds[message.guild.id].users[message.author.id], date_dict)
        if formatted_text.count("\n") > 1:
            await message.channel.send(formatted_text)
        else:
            await message.channel.send("No available times.")
    else:
        await message.channel.send("No Schedule Available.")


@client.command(name='select',
                help="Usage: -select [day] [time] ex. -select Monday 16",
                brief="From your previous meeting list, select a time to do a meeting")
async def select(ctx, day, time):
    message = ctx.message
    day = day.capitalize()
    if all_guilds[message.guild.id].users[message.author.id].last_command[0][day].times[int(time)]:
        string_builder = f"Created a meeting with <@!{message.author.id}>, "
        dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=all_guilds[message.guild.id].users[message.author.id].timezone)
        dt = dt.in_tz("America/Toronto")
        if dt < pendulum.now().in_tz("America/Toronto"):
            dt = dt.add(weeks=1)
        local_meeting = Meeting(dt)
        all_guilds[message.guild.id].users[message.author.id].meetings[local_meeting.meeting_id] = local_meeting
        for user in all_guilds[message.guild.id].users[message.author.id].last_command[1]:
            string_builder += f'<@!{user}>, '
            all_guilds[message.guild.id].users[user].meetings[local_meeting.meeting_id] = local_meeting
        string_builder = string_builder[:-2]
        await message.channel.send(string_builder)
    else:
        await ctx.send("Not a free time.")

@client.command(name="list",
                help='Usage: -list to list all your upcoming meetings',
                brief="List all of your upcoming meetings.")
async def list(ctx):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        if all_guilds[message.guild.id].users[message.author.id].meetings:
            str_builder = "```"
            for meeting in all_guilds[message.guild.id].users[message.author.id].meetings:
                str_builder += all_guilds[message.guild.id].users[message.author.id].meetings[meeting].str_in_tz(all_guilds[message.guild.id].users[message.author.id].timezone) + "\n"
            str_builder += "```"
            await message.channel.send(str_builder)
        else:
            await message.channel.send("No meetings scheduled.")
@client.command(name='remove',
                help='Usage: -remove [meeting id]',
                brief='Removes specified meeting')
async def remove_command(ctx, meeting_id: int):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        if all_guilds[message.guild.id].users[message.author.id].remove_meeting(meeting_id):
            await message.channel.send("Removed meeting.")
        else:
            await message.channel.send("Invalid meeting id.")

    else:
        await message.channel.send("Not a valid user.")

@client.command(name='schedule',
                help='Usage -schedule @user',
                brief='Shows you the schedule of a person')
async def schedule(ctx):
    mention = ctx.message.mentions[0]
    my_user = ctx.author
    if mention.id in all_guilds[ctx.guild.id].users:
        if my_user.id in all_guilds[ctx.guild.id].users:
            await ctx.send(format_date_dictionary(all_guilds[ctx.guild.id].users[my_user.id], all_guilds[ctx.guild.id].users[mention.id].availability))
        else:
            await ctx.send(format_date_dictionary(all_guilds[ctx.guild.id].users[mention.id], all_guilds[ctx.guild.id].users[mention.id].availability))
    else:
        await ctx.send("User has no schedule.")

@client.command(name='cancel',
                help='Usage: -cancel [meeting id]',
                brief='Removes all users from meeting')
async def cancel_command(ctx, meeting_id: int):
    message = ctx.message
    user_list = []
    for users in all_guilds[message.guild.id].users:
        if all_guilds[message.guild.id].users[users].remove_meeting(meeting_id):
            user_list.append(users)
    if user_list:
        str_builder = f"Cancelled meeting with id {meeting_id} for users: "
        for i in user_list:
            str_builder += f'<@!{i}> '
        str_builder = str_builder[:-1]
        await message.channel.send(str_builder)


@client.command(name="commands",
                help='Usage: -commands',
                brief="Returns all commands available")
async def commands(ctx):
    helptext = "```"
    for command in client.commands:
        helptext += f"-{command}: {command.brief}\n"
    helptext+="```"
    await ctx.send(helptext)

@client.command(name='clear',
                help='Usage: -clear',
                brief="Clear all of your meetings (only removes you from the meetings)")
async def clear(ctx):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        all_guilds[message.guild.id].users[message.author.id].meetings = {}

@client.command(name='removeuser',
                help='Usage: -removeuser @user',
                brief='Remove the data of a user from this server')
async def removeuser(ctx):
    user = ctx.message.mentions[0]
    message = ctx.message
    if user.id in all_guilds[ctx.guild.id].users:
        all_guilds[ctx.guild.id].users.pop(user.id)
        await ctx.send('Removed user from data')
    else:
        await ctx.send("User wasn't in data.")


@client.command(name='timezone',
                help='Usage: -timezone [timezone]',
                brief="Manually set your timezone. List of valid timezones: <https://github.com/yoshinoa/csc207_discord_bot/blob/main/timezones.md>")
async def timezone(ctx, local_tz: str):
    message = ctx.message
    if parse_timezone(local_tz):
        if message.author.id in all_guilds[message.guild.id].users:
            all_guilds[message.guild.id].users[message.author.id].timezone = timezone
            await message.channel.send('Your timezone has been updated!')
        else:
            all_guilds[message.guild.id].users[message.author.id] = User(message.author.id, timezone)
            await message.channel.send('Your timezone has been updated!')
    else:
        await message.channel.send('That is an invalid timezone, please consult <https://github.com/yoshinoa/csc207_discord_bot/blob/main/timezones.md> for a list of valid timezones.')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send('Missing a required argument, check usage with -help [command]')
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send('That isn\'t a valid command, check valid commands with -commands')


@client.event
async def on_message(message):
    await client.process_commands(message)
    write_file()


client.run(TOKEN)
