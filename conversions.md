TOMOVE: CANCEL, CLEAR, LEAVE, LIST, MEETING (change to add), SELECT, 


@client.command(name='task',
                help='Modifiers: create, describe, assign, deadline, complete, incomplete, show (complete, )',
                brief='Do various actions with tasks.',
                aliases=['tasks'])
async def task_command(ctx, modifier, *args):
    if modifier == 'create':







##CANCEL
@client.command(name='cancel',
                help='Usage: -cancel [meeting id]',
                brief='Removes all users from meeting')
async def cancel_command(ctx, meeting_id: int):
    message = ctx.message
    meeting = all_guilds[ctx.guild.id].meetings[meeting_id]
    user_list = meeting.return_user_ids()
    all_guilds[ctx.guild.id].meetings.pop(meeting_id)
    meeting.delete_self()
    if user_list:
        str_builder = f"Cancelled meeting with id {meeting_id} for users: "
        for i in user_list:
            str_builder += f'<@!{i}> '
        str_builder = str_builder[:-1]
        await message.channel.send(str_builder)