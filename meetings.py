import pendulum
from itertools import count
import pickle
import os
globvar = 0

def input_from_file(glob: int):
    global globvar
    globvar = glob

class Meeting:
    time: pendulum.datetime
    meeting_id: int

    def __init__(self, time: pendulum.datetime) -> None:
        self.time = time
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
        return self.time.format('dddd Do [of] MMMM HH:mm:ss zz')

    def str_in_tz(self, timezone: str):
        local_tz = self.time.in_tz(timezone)
        return f"ID: {self.meeting_id} {local_tz.format('dddd Do [of] MMMM HH:mm:ss zz')}"

