# csc207_discord_bot

# planned features
* add tasks to shared board
* tasks have properties to help organize (see below)
* assign tasks to person through shared board
* completed tasks board
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

# meeting properties
* ~~possible times~~
* ability to start vote

# values saved to file
~~dict of guilds by guild id that contains a dict that contains:~~
* "task": dict of task_id: task objects
* ~~"meeting": dict of meeting_id: meeting objects~~
* ~~"users": dict of user_id: user_settings~~
