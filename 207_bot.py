import discord
import os
import pickle
from dotenv import load_dotenv
from typing import List, Tuple, Any, Dict
import pendulum
from user import User
from guild import Guild
from meetings import Meeting
import meetings
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone
from globals import init

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
client = discord.Client(intents=intents)
REACTION_IDS, REVERSE_DICT, DAYS_OF_WEEK, all_guilds = init()

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
                all_guilds[payload.guild_id].remove_user(payload.user_id)
                write_file()
        else:
            if payload.user_id in all_guilds[payload.guild_id].users:
                local_user = all_guilds[payload.guild_id].users[payload.user_id]
                time_set = REVERSE_DICT[str(emoji)]
                day_set = all_guilds[payload.guild_id].get_day(payload.message_id)
                local_user.remove_time(time_set, day_set)
                write_file()

def localize_dictionary(user: User, input_dict: Dict[str, Dict[int, bool]]):
    local_availability = {'Monday': {1: False, 2: False, 3: False, 4: False,
                                     5: False, 6: False, 7: False, 8: False,
                                     9: False, 10: False, 11: False, 12: False,
                                     13: False, 14: False, 15: False, 16: False,
                                     17: False, 18: False, 19: False, 20: False,
                                     21: False, 22: False, 23: False, 0: False},
                          'Tuesday': {1: False, 2: False, 3: False, 4: False,
                                      5: False, 6: False, 7: False, 8: False,
                                      9: False, 10: False, 11: False, 12: False,
                                      13: False, 14: False, 15: False,
                                      16: False, 17: False, 18: False,
                                      19: False, 20: False, 21: False,
                                      22: False, 23: False, 0: False},
                          'Wednesday': {1: False, 2: False, 3: False, 4: False,
                                        5: False, 6: False, 7: False, 8: False,
                                        9: False, 10: False, 11: False,
                                        12: False, 13: False, 14: False,
                                        15: False, 16: False, 17: False,
                                        18: False, 19: False, 20: False,
                                        21: False, 22: False, 23: False,
                                        0: False},
                          'Thursday': {1: False, 2: False, 3: False, 4: False,
                                       5: False, 6: False, 7: False, 8: False,
                                       9: False, 10: False, 11: False,
                                       12: False, 13: False, 14: False,
                                       15: False, 16: False, 17: False,
                                       18: False, 19: False, 20: False,
                                       21: False, 22: False, 23: False,
                                       0: False},
                          'Friday': {1: False, 2: False, 3: False, 4: False,
                                     5: False, 6: False, 7: False, 8: False,
                                     9: False, 10: False, 11: False, 12: False,
                                     13: False, 14: False, 15: False, 16: False,
                                     17: False, 18: False, 19: False, 20: False,
                                     21: False, 22: False, 23: False, 0: False},
                          'Saturday': {1: False, 2: False, 3: False, 4: False,
                                       5: False, 6: False, 7: False, 8: False,
                                       9: False, 10: False, 11: False,
                                       12: False, 13: False, 14: False,
                                       15: False, 16: False, 17: False,
                                       18: False, 19: False, 20: False,
                                       21: False, 22: False, 23: False,
                                       0: False},
                          'Sunday': {1: False, 2: False, 3: False, 4: False,
                                     5: False, 6: False, 7: False, 8: False,
                                     9: False, 10: False, 11: False, 12: False,
                                     13: False, 14: False, 15: False, 16: False,
                                     17: False, 18: False, 19: False, 20: False,
                                     21: False, 22: False, 23: False, 0: False}}
    for day in input_dict:
        for times in input_dict[day]:
            dt = pendulum.from_format(f'{day} {times}', 'dddd H', tz="America/Toronto")
            input_vars = dt.in_tz(user.timezone).format('dddd-H').split('-')
            local_availability[input_vars[0]][int(input_vars[1])] = input_dict[day][times]
    return local_availability


def format_date_dictionary(user: User, input_dict: Dict[str, Dict[int, bool]]):
    string = f"Times are in **{user.timezone}**\n"
    local_availability = localize_dictionary(user, input_dict)
    for day in local_availability:
        times = []
        for value in local_availability[day]:
            if local_availability[day][value]:
                times.append(value)
        if times:
            string += day + ": "
            for value in times:
                string += str(value) + ":00, "
            string = string[:-2] + "\n"
    return string


@client.event
async def on_ready():
    await onstart(client)
    await client.change_presence(activity=discord.Activity(name='status', details="Type !commands to see a list of commands", ))
    for server in client.guilds:
        if server.id not in all_guilds:
            await initialize_server(server)
    print(f"{client.user} has connected to discord!")


@client.event
async def on_message(message):
    if message.content[0:8] == '-meeting':
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
        date_dict = all_guilds[message.guild.id].users[message.author.id].compare_with(users_to_check)
        all_guilds[message.guild.id].users[message.author.id].last_command = (localize_dictionary(all_guilds[message.guild.id].users[message.author.id], date_dict), userids)
        await message.channel.send(format_date_dictionary(all_guilds[message.guild.id].users[message.author.id], date_dict))

    elif message.content[0:7] == '-select':
        day = message.content[7:].strip().split(' ')[0]
        time = message.content[7:].strip().split(' ')[1]
        if all_guilds[message.guild.id].users[message.author.id].last_command[0][day][int(time)]:
            string_builder = f"Created a meeting with <@!{message.author.id}>, "
            dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=all_guilds[message.guild.id].users[message.author.id].timezone)
            dt = dt.in_tz("America/Toronto")
            if dt < pendulum.now().in_tz("America/Toronto"):
                dt = dt.add(weeks=1)
            local_meeting = Meeting(dt)
            all_guilds[message.guild.id].users[message.author.id].meetings.append(local_meeting)
            for user in all_guilds[message.guild.id].users[message.author.id].last_command[1]:
                string_builder += f'<@!{user}>, '
                all_guilds[message.guild.id].users[user].meetings.append(local_meeting)
            string_builder = string_builder[:-2]
            await message.channel.send(string_builder)
        else:
            await message.channel.send("That was not a free time.")
    elif message.content[0:5] == '-list':
        if message.author.id in all_guilds[message.guild.id].users:
            for meeting in all_guilds[message.guild.id].users[message.author.id].meetings:
                await message.channel.send(meeting.str_in_tz(all_guilds[message.guild.id].users[message.author.id].timezone))

    elif message.content[0:6] == '-clear':
        if message.author.id in all_guilds[message.guild.id].users:
            all_guilds[message.guild.id].users[message.author.id] = []

    elif message.content[0:9] == '-timezone':
        timezone = message.content[7:].strip().split(' ')[0]
        if len(message.content[7:].strip().split(' ')[0]) > 1:
            await message.channel.send('Too many arguments.')
        else:
            if parse_timezone(timezone):
                if message.author.id in all_guilds[message.guild.id]:
                    all_guilds[message.guild.id].users[message.author.id].timezone = timezone
                    await message.channel.send('Your timezone has been updated!')
                else:
                    all_guilds[message.guild.id].users[message.author.id] = User(message.author.id, timezone)
                    await message.channel.send('Your timezone has been updated!')
            else:
                await message.channel.send('That is an invalid timezone, please consult ')

    elif message.content[0:9] == '!commands':
        await message.channel.send(f"**Commands**:\n"
                                   f"**!partner @member**: create a group with you and your partner, and mark yourselves as ready to start the PAR process with another group.\n"
                                   f"**!individual**: mark yourself as an individual and ready to start the PAR process with another group.\n"
                                   f"**!disband**: disband your current group, and remove yourself from queue, or if you are already paired, remove yourself from the pair.\n"
                                   f"**!groups**: show the current groups.\n"
                                   f"**!findpartner**: *before* you start working on your worksheet, use this command to find another individual that wants to work with someone.\n"
                                   f"**!clear**: clear groups, need administrator permission\n"
                                   f"**!commands**: list commands\n")
    write_file()



client.run(TOKEN)
