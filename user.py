from __future__ import annotations
from typing import Dict, List, Tuple
from weekday import Day, check_overlap
import pendulum
from meetings import Meeting

class User:
    user_id: int
    timezone: str
    availability: Dict[str, Day]
    last_command: Tuple[Dict[str, Dict[int, bool]], List[int]]
    meetings: List[Meeting]

    def __init__(self, user_id: int, timezone: str) -> None:
        self.user_id = user_id
        self.timezone = timezone
        self.availability = {'Monday': Day('Monday'), 'Tuesday': Day('Tuesday'),
                             'Wednesday': Day('Wednesday'),
                             'Thursday': Day('Thursday'),
                             'Friday': Day('Friday'),
                             'Saturday': Day('Saturday'),
                             'Sunday': Day('Sunday')}
        self.last_command = ({}, [])
        self.meetings = []

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            if self.user_id == User.user_id:
                return True
        elif isinstance(other, int):
            if other == self.user_id:
                return True
        return False

    def add_time(self, time: int, day: str) -> None:
        dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=self.timezone)
        input_vars = dt.in_tz("America/Toronto").format('dddd-H').split('-')
        self.availability[input_vars[0]].change(int(input_vars[1]), True)

    def remove_time(self, time: int, day: str) -> None:
        dt = pendulum.from_format(f'{day} {time}', 'dddd H', tz=self.timezone)
        input_vars = dt.in_tz("America/Toronto").format('dddd-H').split('-')
        self.availability[input_vars[0]].change(int(input_vars[1]), False)

    def compare_with(self, other_users: List[User]) -> Dict[str, Dict[int, bool]]:
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
