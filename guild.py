from typing import Dict, List
from user import User

class Guild:
    users: Dict[int, User]
    guild_id: int
    weekday_message_ids: Dict[str, List[int]]

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.users = {}
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

    def add_user(self, user: User) -> None:
        if user.user_id not in self.users:
            self.users[user.user_id] = user

    def remove_user(self, user_id: int) -> None:
        self.users.pop(user_id)


