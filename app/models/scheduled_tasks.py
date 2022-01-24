# app/models/tasks.py

from app import db

from . import save, time_now, delete, GUID


class ScheduledTaskModel(db.Model):
    """
    Create a Scheduled Task table
    All processes that are planned to be executed at a specified or periodically shall be stored here
    Interval shall be saved in seconds
    """
    __tablename__ = 'scheduled_tasks'

    id = db.Column(GUID, primary_key=True, nullable=False)
    name = db.Column(db.String(128), index=True)
    start = db.Column(db.DateTime, nullable=False, default=time_now())
    interval = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    cancelled = db.Column(db.Boolean, default=False)

    @staticmethod
    def retrieve_scheduled_tasks(scheduled_tasks: list):
        if not scheduled_tasks or type(scheduled_tasks) != list:
            return []
        _scheduled_tasks = []
        for position, scheduled_task in enumerate(scheduled_tasks):
            if not scheduled_task or type(scheduled_task) != ScheduledTaskModel:
                continue
            _scheduled_tasks.append(
                {
                    'position': position + 1,
                    'id': scheduled_task.id,
                    'name': scheduled_task.name,
                    'description': scheduled_task.description,
                    'cancelled': scheduled_task.cancelled,
                    'beginning': scheduled_task.start.strftime("%A %b %d, %Y %I:%M %p"),
                    'interval': scheduled_task.interval,
                }
            )
        return _scheduled_tasks

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return '<Scheduled task: {}>'.format(self.id)
