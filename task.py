import pendulum
from structures import User
taskglob = 0

def input_from_file(glob: int):
    global taskglob
    taskglob = glob

class Task:
    assigned_at: pendulum.datetime
    description: str
    due_at: pendulum.datetime
    completion_status: bool
    assignee: User
    assigner: User
    task_id: int

    def __init__(self, description: str, assigner: User, assignee: User):
        self.due_at = None
        self.assigned_at = pendulum.now(tz="EST")
        self.description = description
        self.assigner = assigner
        self.assignee = assignee
        self.completion_status = False
        global taskglob
        self.task_id = taskglob
        taskglob += 1

    def __str__(self):
        str_builder = f"```{self.description}\n"
        if self.due_at:
            str_builder += f"This task is due at {str(self.due_at)}\n"
        str_builder += f'Assigned by {self.assigner} to {self.assignee} at {self.assigned_at} EST'
        return str_builder

    def change_deadline(self, new_date: pendulum.datetime):
        self.due_at = new_date

    def change_assignee(self, new_user: User):
        self.assignee = new_user

    def change_status(self, new_status: bool):
        self.completion_status = new_status

