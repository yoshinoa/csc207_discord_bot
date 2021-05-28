from __future__ import annotations
from typing import Dict, List


def check_overlap(other: List[Day]) -> Dict[int, bool]:
    available_time = {1: True, 2: True, 3: True, 4: True, 5: True,
                      6: True, 7: True, 8: True, 9: True, 10: True,
                      11: True, 12: True, 13: True, 14: True, 15: True,
                      16: True, 17: True, 18: True, 19: True, 20: True,
                      21: True, 22: True, 23: True, 0: True, }
    for item in other:
        for x in available_time:
            if item.times[x] != available_time[x]:
                available_time[x] = False
    return available_time


class Day:
    day_name: str
    times: Dict[int, bool]

    def __init__(self, day_name: str):
        self.day_name = day_name
        self.times = {1: False, 2: False, 3: False, 4: False, 5: False,
                      6: False, 7: False, 8: False, 9: False, 10: False,
                      11: False, 12: False, 13: False, 14: False, 15: False,
                      16: False, 17: False, 18: False, 19: False, 20: False,
                      21: False, 22: False, 23: False, 0: False}

    def change(self, time: int, val: bool) -> None:
        self.times[time] = val
