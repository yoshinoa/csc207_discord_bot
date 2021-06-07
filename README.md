# csc207_discord_bot

# setup
run `pip install -r requirements.txt`

create a .env file in the format 
```
# .env
DISCORD_TOKEN=YOUR_TOKEN_HERE
```

# general commands
`-info [modifier]` modifier can be tasks or meetings

`-meeting` (cannot be used by itself) perform various actions with meetings, look below for more information

`-missing` See members that have yet to set up their timetable

`-removeuser @user` Remove a users data.

`-task` (cannot be used by itself) perform various actions with tasks, look below for more information

`-timezone [timezone]` Manually set a timezone for yourself, check valid timezones at https://github.com/yoshinoa/csc207_discord_bot/blob/main/timezones.md




# meeting function use
General format is `-[meeting|meetings]` `<modifier>` `[args...]`
## meeting modifiers:
`setup @user1 Optional[@user2 @user3...]` Gives meeting times for this user and the tagged other users, must use this before -select.

`select [day] [time]` **REQUIRES SETUP TO BE RUN** From your previous meeting list, select a time to do a meeting -select Monday 16

`leave [MeetingID]` Removes you from specified meeting

`cancel [MeetingID]` Cancels specified meeting

`list` List all of **your** upcoming meetings.

`clear` Clears all your upcoming meetings

`create MM-DD HH` manually create a meeting.



# task function use
General format is `-[task|tasks]` `<modifier>` `[args...]`

## task modifiers: 
`create [task name]` creates a task with taskname and gives you the TaskID

`describe [TaskID] [task description]` adds description to task

`assign [TaskID] [@user]` assigns the @'d user to a task

`deadline [TaskID] [YYYY-M-D] [H]` adds a deadline to task

`complete [TaskID]` marks task as completed (doesn't remove from tracking)

`incomplete [TaskID]` marks task as incomplete

`show <all|complete|incomplete|me|user|unassigned> Optional[args...]` gives you a list of tasks with the arguments passed in. `user` argument requires a `@user`.

# planned features
* ~~add tasks to shared board~~
* ~~tasks have properties to help organize (see below)~~
* ~~assign tasks to person through shared board~~
* ~~completed tasks board~~
* ~~meeting scheduler (list available times and get voting from members)~~
* when reminding members of their tasks, localize to their timezone, default to EST

# user properties
* timezone
* userid


# task properties
* assigned at
* due at
* completion status
* assignee
* reminder date
* change deadline function, change assignee, change status
* description

# meeting properties
* ~~possible times~~
* ability to start vote

# values saved to file
~~dict of guilds by guild id that contains a dict that contains:~~
* "task": dict of task_id: task objects
* ~~"meeting": dict of meeting_id: meeting objects~~
* ~~"users": dict of user_id: user_settings~~
