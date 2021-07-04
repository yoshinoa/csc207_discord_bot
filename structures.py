from __future__ import annotations
import pendulum
from typing import Dict, List, Tuple
from itertools import count
import pickle
import os
globvar = 0
taskglob = 0

def input_from_file(glob: int):
    global globvar
    globvar = glob

class Meeting:
    time: pendulum.datetime
    meeting_id: int
    participants: Dict[int, User]

    def __init__(self, time: pendulum.datetime) -> None:
        self.time = time
        self.participants = {}
        global globvar
        self.meeting_id = globvar
        globvar += 1

    def __eq__(self, other):
        if isinstance(other, Meeting):
            return other.meeting_id == self.meeting_id
        elif isinstance(other, int):
            return other == self.meeting_id
        return False

    def __str__(self):
        strbuilder = f'ID: {self.meeting_id}'
        strbuilder += self.time.format(' dddd Do [of] MMMM HH:mm zz')
        strbuilder += ' with '
        for item in self.participants:
            strbuilder += self.participants[item].username + ", "
        strbuilder = strbuilder[:-2]
        return strbuilder

    def str_in_tz(self, timezone: str):
        local_tz = self.time.in_tz(timezone)
        return f"ID: {self.meeting_id} {local_tz.format('dddd Do [of] MMMM HH:mm:ss zz')}"

    def add_participant(self, user: User):
        self.participants[user.user_id] = user
        user.add_meeting(self)

    def remove_participant(self, user: User):
        if user.user_id in self.participants:
            self.participants.pop(user.user_id)
            return user.remove_meeting(self.meeting_id)

    def delete_self(self):
        for user in self.participants:
            self.participants[user].remove_meeting(self.meeting_id)

    def return_user_ids(self):
        return list(self.participants.keys())

class User:
    user_id: int
    username: str
    timezone: str
    availability: Dict[str, Day]
    last_command: Tuple[Dict[str, Day], List[int]]
    meetings: Dict[int, Meeting]
    tasks: Dict[int, Task]

    def __init__(self, user_id: int, timezone: str, username: str) -> None:
        self.user_id = user_id
        self.username = username
        self.timezone = timezone
        self.availability = {'Monday': Day('Monday'), 'Tuesday': Day('Tuesday'),
                             'Wednesday': Day('Wednesday'),
                             'Thursday': Day('Thursday'),
                             'Friday': Day('Friday'),
                             'Saturday': Day('Saturday'),
                             'Sunday': Day('Sunday')}
        self.last_command = ({}, [])
        self.meetings = {}

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            if self.user_id == other.user_id:
                return True
        elif isinstance(other, int):
            if other == self.user_id:
                return True
        return False

    def get_mention(self) -> str:
        return f'<@{self.user_id}>'

    def add_time(self, time: int, day: str) -> None:
        dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=self.timezone)
        input_vars = dt.in_tz("America/Toronto").format('dddd-H').split('-')
        self.availability[input_vars[0]].change(int(input_vars[1]), True)

    def remove_time(self, time: int, day: str) -> None:
        dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=self.timezone)
        input_vars = dt.in_tz("America/Toronto").format('dddd-H').split('-')
        self.availability[input_vars[0]].change(int(input_vars[1]), False)

    def compare_with(self, other_users: List[User]) -> Dict[str, Day]:
        return_dict = {}
        for day in self.availability:
            day_list = [self.availability[day]]
            for users in other_users:
                day_list.append(users.availability[day])
            return_dict[day] = check_overlap(day_list)
        return return_dict

    def convert_back(self):
        local_availability = {}
        for day in self.availability:
            for times in self.availability[day].times:
                dt = pendulum.from_format(f'{day} {times}', 'dddd H', tz="America/Toronto")
                input_vars = dt.in_tz(self.timezone).format('dddd-H').split('-')
                local_availability[input_vars[0]].change(int(input_vars[1]), True)

    def remove_meeting(self, meeting_id: int) -> bool:
        if meeting_id in self.meetings:
            self.meetings.pop(meeting_id)
            return True
        return False

    def add_task(self, new_task: Task):
        self.tasks[new_task.task_id] = new_task

    def add_meeting(self, meeting: Meeting):
        self.meetings[meeting.meeting_id] = meeting

    def true_dict(self) -> Dict[str, List[int]]:
        new_dict = {}
        local_availability = self.localize_dictionary(self.availability)
        for days in local_availability:
            if local_availability[days].convert():
                new_dict[days] = local_availability[days].convert()
        return new_dict

    def localize_dictionary(self, input_dict: Dict[str, Day]) -> Dict[str, Day]:
        local_availability = {'Monday': Day('Monday'),
                              'Tuesday': Day('Tuesday'),
                              'Wednesday': Day('Wednesday'),
                              'Thursday': Day('Thursday'),
                              'Friday': Day('Friday'),
                              'Saturday': Day('Saturday'),
                              'Sunday': Day('Sunday')}
        for day in input_dict:
            for times in input_dict[day].times:
                dt = pendulum.from_format(f'{day} {times}', 'dddd H', tz="America/Toronto")
                input_vars = dt.in_tz(self.timezone).format('dddd-H').split('-')
                local_availability[input_vars[0]].change(int(input_vars[1]), input_dict[day].times[times])
        return local_availability

def check_overlap(other: List[Day]) -> Day:
    temp_day = Day(other[0].day_name)
    temp_day.times = {0: True, 1: True, 2: True, 3: True, 4: True, 5: True,
                      6: True, 7: True, 8: True, 9: True, 10: True,
                      11: True, 12: True, 13: True, 14: True, 15: True,
                      16: True, 17: True, 18: True, 19: True, 20: True,
                      21: True, 22: True, 23: True}
    for item in other:
        for x in temp_day.times:
            if item.times[x] != temp_day.times[x]:
                temp_day.times[x] = False
    return temp_day


class Day:
    day_name: str
    times: Dict[int, bool]

    def __init__(self, day_name: str):
        self.day_name = day_name
        self.times = {0: False, 1: False, 2: False, 3: False, 4: False, 5: False,
                      6: False, 7: False, 8: False, 9: False, 10: False,
                      11: False, 12: False, 13: False, 14: False, 15: False,
                      16: False, 17: False, 18: False, 19: False, 20: False,
                      21: False, 22: False, 23: False}

    def change(self, time: int, val: bool) -> None:
        self.times[time] = val

    def convert(self) -> List[int]:
        list_builder = []
        for x in self.times:
            if self.times[x]:
                list_builder.append(x)
        return list_builder

class Guild:
    users: Dict[int, User]
    guild_id: int
    weekday_message_ids: Dict[str, List[int]]
    tasks: Dict[int, Task]
    meetings: Dict[int, Meeting]
    channel_id: int
    timezone_id: int

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.users = {}
        self.tasks = {}
        self.meetings = {}
        self.weekday_message_ids = {'Monday': [], 'Tuesday': [],
                                    'Wednesday': [], 'Thursday': [],
                                    'Friday': [], 'Saturday': [], 'Sunday': []}


    def __eq__(self, other) -> bool:
        if isinstance(other, Guild):
            return other.guild_id == self.guild_id
        elif isinstance(other, int):
            return other == self.guild_id
        return False

    def get_day(self, message_id: int) -> str:
        for key in self.weekday_message_ids:
            if message_id in self.weekday_message_ids[key]:
                return key
        return ''

    def add_message_id(self, new_id: int, day: str) -> None:
        self.weekday_message_ids[day].append(new_id)

    def set_timezone_id(self, new_id: int):
        self.timezone_id = new_id

    def add_user(self, user: User) -> None:
        if user.user_id not in self.users:
            self.users[user.user_id] = user

    def add_user_to_task(self, task: Task, user: User) -> bool:
        if task.task_id in self.tasks:
            task.change_assignee(user)
            user.add_task(task)
            return True
        return False


    def remove_user(self, user_id: int) -> None:
        for meeting in self.meetings:
            self.meetings[meeting].remove_participant(self.users[user_id])
        self.users.pop(user_id)

    def add_meeting(self, meeting: Meeting):
        if meeting.meeting_id not in self.meetings:
            self.meetings[meeting.meeting_id] = meeting

    def set_channel_id(self, id: int):
        self.channel_id = id

    def verify_meetings(self):
        if self.meetings:
            for meetings in self.meetings:
                if not self.meetings[meetings].participants:
                    self.meetings.pop(meetings)

    def add_task(self, new_task: Task):
        self.tasks[new_task.task_id] = new_task

    def remove_task(self, taskID: int):
        self.tasks.pop(taskID, None)

    def get_tasks_completion(self, input: bool):
        task_list = []
        for tasks in self.tasks:
            if self.tasks[tasks].completion_status == input:
                task_list.append(self.tasks[tasks])
        return task_list

    def get_tasks_unassigned(self):
        task_list = []
        for tasks in self.tasks:
            if self.tasks[tasks].assignee is None:
                task_list.append(self.tasks[tasks])
        return task_list
    def get_tasks_user(self, user: User):
        complete = []
        incomplete = []
        for tasks in self.tasks:
            if user in self.tasks[tasks].assignee:
                if not self.tasks[tasks].completion_status:
                    incomplete.append(self.tasks[tasks])
                else:
                    complete.append(self.tasks[tasks])
        return complete, incomplete

    def show_meetings(self):
        if self.meetings:
            str_builder = "```"
            for item in self.meetings:
                str_builder += str(self.meetings[item]) + '\n'
            str_builder += '```'
            return str_builder
        else:
            return "No meetings."


class Task:
    assigned_at: pendulum.datetime
    description: str
    due_at: pendulum.datetime
    completion_status: bool
    assignee: List[User]
    assigner: User
    task_id: int
    task_name: str
    completed_on: pendulum.datetime

    def __init__(self, name: str, assigner: User):
        self.due_at = None
        self.task_name = name
        self.assigned_at = pendulum.now(tz="EST")
        self.description = ""
        self.assigner = assigner
        self.assignee = []
        self.completion_status = False
        self.completed_on = None
        global taskglob
        self.task_id = taskglob
        taskglob += 1

    def __str__(self):
        if self.completion_status:
            loc_completion = f"COMPLETE AS OF {self.completed_on.format('MM-D HH:mm zz')}"
        else:
            loc_completion = 'INCOMPLETE'
        str_builder = f"ID: {self.task_id}, {loc_completion}\nNAME: {self.task_name}\nDESCRIPTION: {self.description}\n"
        if not self.completion_status and self.due_at:
            str_builder += f"This task is incomplete and due at {str(self.due_at.format('MM-D HH:mm zz'))}\n"
        if self.assignee:
            str_builder += f"Assigned by {self.assigner.username} to "
            for user in self.assignee:
                str_builder += user.username + " and "
            str_builder = str_builder[:-4]
            str_builder += f"on {self.assigned_at.format('MM-D HH:mm zz')}"
        else:
            str_builder += f"Initialized by {self.assigner.username} on {self.assigned_at.format('MM-D HH:mm zz')}, currently unassigned."
        return str_builder

    def change_deadline(self, new_date: pendulum.datetime):
        self.due_at = new_date

    def change_assignee(self, new_user: User):
        if new_user not in self.assignee:
            self.assignee.append(new_user)

    def remove_assignee(self, new_user):
        if new_user in self.assignee:
            self.assignee.remove(new_user)

    def change_status(self, new_status: bool):
        if new_status:
            self.completed_on = pendulum.now(tz="EST")
        else:
            self.completed_on = None
        self.completion_status = new_status

    def set_description(self, description: str):
        self.description = description
