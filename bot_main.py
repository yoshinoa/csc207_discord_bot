import discord
from discord.ext import commands
import os
import pickle
from dotenv import load_dotenv
from typing import Dict, List
import pendulum
from structures import Guild, Day, User, Meeting, Task
import structures
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone
import globals


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
client = commands.Bot(intents=intents, command_prefix='-')
REACTION_IDS, REVERSE_DICT, DAYS_OF_WEEK, all_guilds = globals.init()


def parse_timezone(loc_time: str) -> str:
    """
    Given a string, return the same string back if this str can be parsed
    as a timezone
    """
    try:
        now = pendulum.now("EST")
        now.in_timezone(loc_time)
        return loc_time
    except InvalidTimezone:
        return ''


def format_date_dictionary(local_user: User, input_dict: Dict[str, Day]):
    string = f"Times are in **{local_user.timezone}**\n```"
    local_availability = local_user.localize_dictionary(input_dict)
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


def onstart():
    if os.path.exists("session.pickle"):
        with open("session.pickle", 'rb') as pickle_file:
            pickle_data = pickle.load(pickle_file)
        global all_guilds
        all_guilds = pickle_data['initialized_guilds']
        structures.globvar = pickle_data['globvar']
        structures.taskglob = pickle_data['taskglob']


def write_file():
    writing_dict = {"initialized_guilds": all_guilds,
                    'globvar': structures.globvar,
                    'taskglob': structures.taskglob}
    with open("session.pickle", "wb") as pickle_file:
        pickle.dump(writing_dict, pickle_file)


def task_list_to_string(task_list: List[Task]) -> str:
    strbuilder = "```"
    for item in task_list:
        strbuilder += str(item) + "\n\n"
    strbuilder += '```'
    if strbuilder == "``````":
        return "No tasks."
    else:
        return strbuilder


async def initialize_server(guild: discord.guild):
    new_guild = Guild(guild.id)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False)}
    channel = await guild.create_text_channel('availability',
                                              overwrites=overwrites)
    new_guild.set_channel_id(channel.id)
    await channel.send(f'In order to use commands react to the messages here!')
    message = await channel.send(
        f'**Select your timezone.** If your timezone isn\'t here use the command -timezone (your timezone)')
    new_guild.set_timezone_id(message.id)
    for TZ in ['America/Toronto', 'America/Vancouver', 'Asia/Tokyo',
               'Asia/Seoul', 'Asia/Shanghai', 'Canada/Central']:
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
    await channel.set_permissions(guild.default_role, read_messages=True)
    write_file()
    print(f"initialized guild {guild.name}")


async def remove_all_reactions(payload, local_user: discord.User):
    remove_var = False
    try:
        guildid = payload.guild.id
        channel = client.get_channel(all_guilds[guildid].channel_id)
        local_dict = all_guilds[payload.guild.id].users[local_user.id].true_dict()
        remove_var = True
    except:
        guildid = payload.guild_id
        channel = client.get_channel(payload.channel_id)
        local_dict = all_guilds[payload.guild_id].users[local_user.id].true_dict()
    new_dict = {}
    for x in local_dict:
        for i in local_dict[x]:
            if i > 20:
                if all_guilds[guildid].weekday_message_ids[x][1] in new_dict:
                    new_dict[
                        all_guilds[guildid].weekday_message_ids[x][1]].append(
                        REACTION_IDS[i])
                else:
                    new_dict[all_guilds[guildid].weekday_message_ids[x][1]] = [
                        REACTION_IDS[i]]
            else:
                if all_guilds[guildid].weekday_message_ids[x][0] in new_dict:
                    new_dict[
                        all_guilds[guildid].weekday_message_ids[x][0]].append(
                        REACTION_IDS[i])
                else:
                    new_dict[all_guilds[guildid].weekday_message_ids[x][0]] = [
                        REACTION_IDS[i]]
    if remove_var:
        if all_guilds[guildid].users[local_user.id].timezone in REACTION_IDS:
            timezone_message = await channel.fetch_message(
                all_guilds[guildid].timezone_id)
            await timezone_message.remove_reaction(
                REACTION_IDS[all_guilds[guildid].users[local_user.id].timezone], local_user)
    for item in new_dict:
        local_message = await channel.fetch_message(item)
        for item2 in new_dict[item]:
            await local_message.remove_reaction(item2, local_user)


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if client.user.id != payload.user_id and all_guilds[payload.guild_id].channel_id == payload.channel_id:
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        actual_user = client.get_user(payload.user_id)
        emoji = payload.emoji
        if str(emoji) not in REVERSE_DICT:
            await message.remove_reaction(emoji, actual_user)
        elif 'Select your timezone.' in message.content:
            if payload.user_id in all_guilds[payload.guild_id].users:
                await message.remove_reaction(emoji, actual_user)
            else:
                if payload.member.nick is not None:
                    all_guilds[payload.guild_id].add_user(
                        User(payload.user_id, REVERSE_DICT[str(emoji)],
                             payload.member.nick))
                else:
                    all_guilds[payload.guild_id].add_user(
                        User(payload.user_id, REVERSE_DICT[str(emoji)],
                             payload.member.display_name))
        else:
            if payload.user_id in all_guilds[payload.guild_id].users:
                local_user = all_guilds[payload.guild_id].users[payload.user_id]
                time_set = REVERSE_DICT[str(emoji)]
                day_set = all_guilds[payload.guild_id].get_day(
                    payload.message_id)
                local_user.add_time(time_set, day_set)
            else:
                await message.remove_reaction(emoji, actual_user)


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    actual_user = client.get_user(payload.user_id)
    emoji = payload.emoji
    if str(emoji) in REVERSE_DICT:
        if 'Select your timezone.' in message.content:
            if payload.user_id in all_guilds[payload.guild_id].users and \
                    all_guilds[payload.guild_id].users[payload.user_id]. \
                    timezone == REVERSE_DICT[str(emoji)]:
                await remove_all_reactions(payload, actual_user)
                all_guilds[payload.guild_id].remove_user(payload.user_id)
                write_file()
        else:
            if payload.user_id in all_guilds[payload.guild_id].users:
                local_user = all_guilds[payload.guild_id].users[payload.user_id]
                time_set = REVERSE_DICT[str(emoji)]
                day_set = all_guilds[payload.guild_id].get_day(
                    payload.message_id)
                local_user.remove_time(time_set, day_set)
                write_file()


@client.event
async def on_ready():
    onstart()
    await client.change_presence(activity=discord.Game(name="-help"))
    for server in client.guilds:
        if server.id not in all_guilds:
            await initialize_server(server)
    print(f"{client.user} has connected to discord!")


@client.event
async def on_guild_join(guild):
    await initialize_server(guild)
    write_file()



@client.group(name='meeting',
              aliases=['meetings'],
              help='perform various actions with meetings, type -help meeting/meetings for more info.')
async def meeting(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Invalid meeting command.')


@meeting.command(name='create',
                 help='manually create a meeting in EST',
                 brief='usage: -create MM-DD HH')
async def create_meeting(context, date: str, time: str):
    if context.message.author.id in all_guilds[context.guild.id].users:
        message = context.message
        date = pendulum.from_format(f'{date} {time}', 'MM-DD HH', tz="EST")
        string_builder = f"Created a meeting with <@!{message.author.id}>."
        if date < pendulum.now().in_tz("America/Toronto"):
            await context.send('Invalid time.')
        local_meeting = Meeting(date)
        local_meeting.add_participant(
            all_guilds[message.guild.id].users[message.author.id])
        all_guilds[message.guild.id].add_meeting(local_meeting)
        string_builder += f' ID: {local_meeting.meeting_id}'
        await context.send(string_builder)
    else:
        await context.send('Please set your schedule before creating meetings.')


@meeting.command(name='invite',
                 help='invite users to a meeting',
                 brief='usage: -invite meetingID @user1 @user2')
async def invite_meeting(context, meetingID: int, *args):
    message = context.message
    if len(message.mentions) >= 1:
        for local_user in message.mentions:
            if local_user.id not in all_guilds[message.guild.id].users:
                await context.send("Not a registered user.")
            else:
                all_guilds[message.guild.id].users[local_user.id].add_meeting(all_guilds[message.guild.id].meetings[meetingID])
                all_guilds[message.guild.id].meetings[meetingID].add_participant(all_guilds[message.guild.id].users[local_user.id])
                await context.send("Added user to meeting!")
    else:
        await context.send('No users specified.')



@meeting.command(name='setup',
                 help="Usage: -meeting @user1 @user2 ex. -meeting @132ads",
                 brief="Gives meeting times for this user and the tagged other users.")
async def setup(context):
    message = context.message
    users_to_check = []
    userids = []
    try:
        message.mentions[0]
    except IndexError:
        await message.channel.send(
            f"Input did not contain another user, please @ them.")
    for local_user in message.mentions:
        if message.guild.id in all_guilds and local_user.id in \
                all_guilds[message.guild.id].users:
            users_to_check.append(all_guilds[message.guild.id].users[local_user.id])
            userids.append(local_user.id)
        else:
            await message.channel.send(
                f"{user.name} hasn't set their schedule.")
    if userids:
        date_dict = all_guilds[message.guild.id].users[
            message.author.id].compare_with(users_to_check)
        all_guilds[message.guild.id].users[message.author.id].last_command = \
            all_guilds[message.guild.id].users[
                message.author.id].localize_dictionary(date_dict), userids
        formatted_text = format_date_dictionary(
            all_guilds[message.guild.id].users[message.author.id], date_dict)
        if formatted_text.count("\n") > 1:
            await message.channel.send(formatted_text)
        else:
            await message.channel.send("No available times.")
    else:
        await message.channel.send("No Schedule Available.")


@meeting.command(name='select',
                 help="Usage: -select [day] [time] ex. -select Monday 16",
                 brief="From your previous meeting list, select a time to do a meeting")
async def select(ctx, day, time):
    message = ctx.message
    day = day.capitalize()
    if all_guilds[message.guild.id].users[message.author.id].\
            last_command[0][day].times[int(time)]:
        string_builder = f"Created a meeting with <@!{message.author.id}>, "
        dt = pendulum.from_format(f'{day} {time}', 'dddd H',
                                  tz=all_guilds[message.guild.id].users[
                                      message.author.id].timezone)
        dt = dt.in_tz("America/Toronto")
        if dt < pendulum.now().in_tz("America/Toronto"):
            dt = dt.add(weeks=1)
        local_meeting = Meeting(dt)
        local_meeting.add_participant(
            all_guilds[message.guild.id].users[message.author.id])
        all_guilds[message.guild.id].add_meeting(local_meeting)
        for local_user in \
                all_guilds[message.guild.id].users[
                    message.author.id].last_command[1]:
            string_builder += f'<@!{local_user}>, '
            local_meeting.add_participant(
                all_guilds[message.guild.id].users[local_user])
        string_builder = string_builder[:-2]
        string_builder += f' ID: {local_meeting.meeting_id}.'
        await message.channel.send(string_builder)
    else:
        await ctx.send("Not a free time.")


@meeting.command(name="list",
                 help='Usage: -list to list all your upcoming meetings',
                 brief="List all of your upcoming meetings.")
async def command_list(ctx):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        if all_guilds[message.guild.id].users[message.author.id].meetings:
            str_builder = "```"
            for local_meeting in all_guilds[message.guild.id].users[
                message.author.id].meetings:
                str_builder += \
                    all_guilds[message.guild.id].users[
                        message.author.id].meetings[
                        local_meeting].str_in_tz(all_guilds[message.guild.id].users[
                                               message.author.id].timezone) + "\n"
            str_builder += "```"
            await message.channel.send(str_builder)
        else:
            await message.channel.send("No meetings scheduled.")


@meeting.command(name='leave',
                 help='Usage: -leave [meeting id]',
                 brief='Removes specified meeting')
async def remove_command(ctx, meeting_id: int):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        ref_user = all_guilds[message.guild.id].users[message.author.id]
        if all_guilds[message.guild.id].meetings[meeting_id].remove_participant(
                ref_user):
            await message.channel.send("Removed you from meeting.")
        else:
            await message.channel.send("Invalid meeting id.")
    else:
        await message.channel.send("You aren't a registered user.")


@meeting.command(name='cancel',
                 help='Usage: -cancel [meeting id]',
                 brief='Removes all users from meeting')
async def cancel_command(ctx, meeting_id: int):
    message = ctx.message
    local_meeting = all_guilds[ctx.guild.id].meetings[meeting_id]
    user_list = local_meeting.return_user_ids()
    all_guilds[ctx.guild.id].meetings.pop(meeting_id)
    local_meeting.delete_self()
    if user_list:
        str_builder = f"Cancelled meeting with id {meeting_id} for users: "
        for i in user_list:
            str_builder += f'<@!{i}> '
        str_builder = str_builder[:-1]
        await message.channel.send(str_builder)


@meeting.command(name='schedule',
                 help='Usage -schedule @user',
                 brief='Shows you the schedule of a person')
async def schedule(ctx):
    try:
        mention = ctx.message.mentions[0]
        my_user = ctx.author
        if mention.id in all_guilds[ctx.guild.id].users:
            if my_user.id in all_guilds[ctx.guild.id].users:
                await ctx.send(format_date_dictionary(
                    all_guilds[ctx.guild.id].users[my_user.id],
                    all_guilds[ctx.guild.id].users[mention.id].availability))
            else:
                await ctx.send(format_date_dictionary(
                    all_guilds[ctx.guild.id].users[mention.id],
                    all_guilds[ctx.guild.id].users[mention.id].availability))
        else:
            await ctx.send("User has no schedule.")
    except IndexError:
        await ctx.send("Not enough arguments. Check -help schedule for help.")


@meeting.command(name='clear',
                 help='Usage: -clear',
                 brief="Clear all of your meetings (only removes you from the "
                       "meetings)")
async def clear(ctx):
    message = ctx.message
    if message.author.id in all_guilds[message.guild.id].users:
        for meetingid in all_guilds[message.guild.id].users[
            message.author.id].meetings:
            all_guilds[message.guild.id].users[message.author.id].meetings[
                meetingid].remove_participant(
                all_guilds[message.guild.id].users[message.author.id])
        await ctx.send('Removed from all meetings.')
    else:
        await ctx.send('Not a registered user')


# @meeting.command(name='add',
#                  help='Usage: -add [MeetingID] [TaskID]')


@client.command(name='removeuser',
                help='Remove the data of a user from this server (Requires '
                     'Admin)',
                brief='Usage: -removeuser @user')
@commands.has_permissions(administrator=True)
async def removeuser(ctx):
    local_user = ctx.message.mentions[0]
    if local_user.id in all_guilds[ctx.guild.id].users:
        await remove_all_reactions(ctx, local_user)
        all_guilds[ctx.guild.id].remove_user(local_user.id)
        await ctx.send('Removed user from data')
    else:
        await ctx.send("User wasn't in data.")


@client.group(name='task',
              help='perform various actions with tasks, type -help task for '
                   'more info',
              aliases=['tasks'])
async def task_group(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid subcommand for task.")


@task_group.command(name='create',
                    help='create [task name]` creates atask  with taskname '
                         'and gives you the TaskID')
async def create(ctx, *args):
    flatten = []
    for item in args:
        flatten.append(item)
    name = ' '.join([str(elem) for elem in flatten])
    assigner = all_guilds[ctx.guild.id].users[ctx.author.id]
    localtask = Task(name, assigner)
    all_guilds[ctx.guild.id].add_task(localtask)
    await ctx.send(f"Task with TaskID **{localtask.task_id}** was created")

@task_group.command(name='unassign',
                    help='unassign [task id] @user')
async def unassign(ctx, taskid: int):
    try:
        if taskid in all_guilds[ctx.guild.id].tasks:
            if ctx.message.mentions[0].id in all_guilds[ctx.guild.id].users:
                assignee = all_guilds[ctx.guild.id].users[
                    ctx.message.mentions[0].id]
                all_guilds[ctx.guild.id].tasks[taskid].remove_assignee(assignee)
                await ctx.send(
                    f'Successfully removed <@{ctx.message.mentions[0].id}>.')
            else:
                await ctx.send(
                    f'<@{ctx.message.mentions[0].id}> has not yet setup their '
                    f'schedule.')
        else:
            await ctx.send("Invalid task id.")
    except ValueError:
        await ctx.send("Invalid or missing task id.")

@task_group.command(name='delete',
                    help='delete [task id]')
async def delete(ctx, taskid: int):
    curr_guild = all_guilds[ctx.guild.id]
    task = curr_guild.tasks[taskid]
    for user in task.assignee:
        del user.tasks[taskid]
    curr_guild.remove_task(taskid)
    await ctx.send("Deleted task!")


@task_group.command(name='describe',
                    help='`describe [TaskID] [task description]` adds '
                         'description to task')
async def describe(ctx, taskid: int, *args):
    if taskid in all_guilds[ctx.guild.id].tasks:
        flatten = []
        for item in args:
            flatten.append(item)
        description = ' '.join([str(elem) for elem in flatten])
        all_guilds[ctx.guild.id].tasks[taskid].set_description(description)
        await ctx.send('Description set successfully.')
    else:
        await ctx.send("Invalid task id.")


@task_group.command(name='assign',
                    help='`assign [TaskID] [@user]` assigns the @\'d user to '
                         'a task')
async def assign(ctx, taskid: int):
    try:
        if taskid in all_guilds[ctx.guild.id].tasks:
            if ctx.message.mentions[0].id in all_guilds[ctx.guild.id].users:
                assignee = all_guilds[ctx.guild.id].users[
                    ctx.message.mentions[0].id]
                all_guilds[ctx.guild.id].tasks[taskid].change_assignee(assignee)
                await ctx.send(
                    f'Successfully assigned to <@{ctx.message.mentions[0].id}>.')
            else:
                await ctx.send(
                    f'<@{ctx.message.mentions[0].id}> has not yet setup their '
                    f'schedule.')
        else:
            await ctx.send("Invalid task id.")
    except ValueError:
        await ctx.send("Invalid or missing task id.")


@task_group.command(name='deadline',
                    help='`deadline [TaskID] [YYYY-M-D] [H]` adds a deadline '
                         'to task')
async def deadline(ctx, taskid: int, date: str, time: str):
    deadline_date = pendulum.from_format(f'{date} {time}', 'YYYY-M-D H',
                                         tz='est')
    if taskid in all_guilds[ctx.guild.id].tasks:
        all_guilds[ctx.guild.id].tasks[taskid].change_deadline(deadline_date)
        await ctx.send(
            f"Deadline successfully set to "
            f"{deadline_date.format(' dddd Do [of] MMMM HH:mm zz')}")
    else:
        await ctx.send("Invalid task id.")


@task_group.command(name='complete',
                    help='`complete [TaskID]` marks task as completed ('
                         'doesn\'t remove from tracking)')
async def complete(ctx, taskid: int):
    if taskid in all_guilds[ctx.guild.id].tasks:
        all_guilds[ctx.guild.id].tasks[taskid].change_status(True)
        await ctx.send(
            f'Task {all_guilds[ctx.guild.id].tasks[taskid].task_name} completed'
            f' successfully')
    else:
        await ctx.send("Invalid task id.")


@task_group.command(name='incomplete',
                    help='`incomplete [TaskID]` marks task as incomplete')
async def incomplete(ctx, taskid: int):
    if taskid in all_guilds[ctx.guild.id].tasks:
        all_guilds[ctx.guild.id].tasks[taskid].change_status(False)
        await ctx.send(
            f'Task {all_guilds[ctx.guild.id].tasks[taskid].task_name} set to'
            f' incomplete.')
    else:
        await ctx.send("Invalid task id.")


@task_group.group(name='show',
                  help='`show <all|complete|incomplete|me|user|unassigned>'
                       ' Optional[args...]` gives you a list of tasks with'
                       ' the arguments passed in. `user` argument requires'
                       ' a `@user`.')
async def show(ctx):
    if ctx.invoked_subcommand is None:
        ctx.send("Invalid subcommand for task.")


@show.command(name='all',
              help='Shows task completion of all tasks in server.')
async def command_all(ctx):
    task_list = all_guilds[ctx.guild.id].get_tasks_completion(True) + \
                all_guilds[ctx.guild.id].get_tasks_completion(False)
    await ctx.send(task_list_to_string(task_list))


@show.command(name='complete',
              help='Shows complete tasks.')
async def complete(ctx):
    task_list = all_guilds[ctx.guild.id].get_tasks_completion(True)
    await ctx.send(task_list_to_string(task_list))


@show.command(name='incomplete',
              help='Shows incomplete tasks.')
async def incomplete(ctx):
    task_list = all_guilds[ctx.guild.id].get_tasks_completion(False)
    await ctx.send(task_list_to_string(task_list))


@show.command(name='user',
              help='Shows all tasks assigned to @user')
async def user(ctx):
    local_user = all_guilds[ctx.guild.id].users[ctx.message.mentions[0].id]
    finished, unfinished = all_guilds[ctx.guild.id].get_tasks_user(local_user)
    strbuilder = "```Complete:\n"
    for item in finished:
        strbuilder += str(item) + '\n'
    strbuilder += "Incomplete:\n"
    for item in unfinished:
        strbuilder += str(item) + '\n'
    strbuilder += '```'
    await ctx.send(strbuilder)


@show.command(name='unassigned',
              help='Shows all unassigned tasks')
async def unassigned(ctx):
    await ctx.send(
        task_list_to_string(all_guilds[ctx.guild.id].get_tasks_unassigned()))


@show.command(name='me',
              help='Shows status of your own tasks')
async def me(ctx):
    local_user = all_guilds[ctx.guild.id].users[ctx.message.author.id]
    completed, incompleted = all_guilds[ctx.guild.id].get_tasks_user(local_user)
    strbuilder = "```Complete:\n"
    for item in completed:
        strbuilder += str(item) + '\n'
    strbuilder += "\nIncomplete:\n"
    for item in incompleted:
        strbuilder += str(item) + '\n'
    strbuilder += '```'
    await ctx.send(strbuilder)


@client.command(name='timezone',
                help='Manually set your timezone. List of valid timezones: <https://github.com/yoshinoa/csc207_discord_bot/blob/main/timezones.md>',
                brief="Usage: -timezone [timezone]")
async def timezone(ctx, local_tz: str):
    message = ctx.message
    if parse_timezone(local_tz):
        if message.author.id in all_guilds[message.guild.id].users:
            all_guilds[message.guild.id].users[
                message.author.id].timezone = timezone
            await message.channel.send('Your timezone has been updated!')
        else:
            all_guilds[message.guild.id].users[message.author.id] = User(
                message.author.id, timezone, ctx.author.nick)
            await message.channel.send('Your timezone has been updated!')
    else:
        await message.channel.send(
            'That is an invalid timezone, please consult <https://github.com/yoshinoa/csc207_discord_bot/blob/main/timezones.md> for a list of valid timezones.')


@client.command(name='info',
                help='Show a list of tasks or meetings for this server',
                brief='Usage: -info [modifier], modifier can be tasks or meetings')
async def dump_items(ctx, modifier: str):
    if modifier in ('tasks', 'Tasks'):
        task_list = all_guilds[ctx.guild.id].get_tasks_completion(True) + \
                    all_guilds[ctx.guild.id].get_tasks_completion(False)
        await ctx.send(task_list_to_string(task_list))
    elif modifier in ('meetings', 'Meetings'):

        await ctx.send(all_guilds[ctx.guild.id].show_meetings())
    else:
        await ctx.send("Invalid modifier.")


@client.command(name='convert')
async def convert(ctx):
    guild = all_guilds[ctx.guild.id]
    for task in guild.tasks:
        guild.tasks[task].assignee = []
    await ctx.send("Converted")

@client.command(name='missing',
                help='Shows all the users without a schedule on the server.',
                brief='Usage: -missing')
async def list_users(ctx):
    non_user_list = "```"
    for users in ctx.guild.members:
        if users.id != client.user.id and users.id not in all_guilds[ctx.guild.id].users:
            non_user_list += users.display_name + "\n"
    non_user_list += '```'
    await ctx.send(non_user_list)


@client.command(name='github',
                help='https://github.com/yoshinoa/csc207_discord_bot/blob/main/README.md',
                brief='https://github.com/yoshinoa/csc207_discord_bot/blob/main/README.md')
async def lol(ctx):
    await ctx.send('<https://github.com/yoshinoa/csc207_discord_bot/blob/main/README.md>')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send(
            'Missing a required argument, check usage with -help [command]')
    elif isinstance(error, discord.ext.commands.errors.BadArgument):
        await ctx.send("Invalid argument, check usage with -help [command]")
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(
            'That isn\'t a valid command, check valid commands with -help')
    elif isinstance(error, KeyError):
        await ctx.send(
            "It's likely you haven't initalized yourself yet, set your timezone in the availability channel or type -timezone [timezones]")
    elif isinstance(error, discord.ext.commands.errors.MissingPermissions):
        await ctx.send("You're missing the permission to run this command.")
    else:
        print(error, type(error))


@client.event
async def on_message(message):
    if message.author.id != client.user.id:
        await client.process_commands(message)
        all_guilds[message.guild.id].verify_meetings()
        write_file()


client.run(TOKEN)
