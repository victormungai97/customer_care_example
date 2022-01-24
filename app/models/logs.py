# app/models/logs.py

import uuid

from flask import request

from app import db

from . import save, time_now, delete, GUID


class LogModel(db.Model):
    """
    Create a Logging table
    This will be used to save log messages
    """

    __tablename__ = 'logs'

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4(), )
    message = db.Column('Message', db.Text, default='', nullable=False)
    level = db.Column('Level', db.Text, nullable=False, default='info')
    timestamp = db.Column(db.DateTime, default=time_now(), nullable=False, )
    source = db.Column('Source', db.Text, nullable=False, default='')
    platform = db.Column('Platform', db.Text, nullable=True, )
    created_on = db.Column(db.DateTime, default=time_now(), )
    log_file = db.Column('Log File', db.Text, default="")

    @staticmethod
    def retrieve_logs(logs: list):
        if not logs or type(logs) != list:
            return []
        _logs = []
        from ..utils import Helper
        base_url = Helper.parse_url(request.url)
        for position, log in enumerate(logs):
            if not log or type(log) != LogModel:
                continue
            if Helper.detect_url(log.log_file):
                log_file = log.log_file
            else:
                log_file = f'{base_url}{log.log_file}'
            _logs.append(
                {
                    "id": log.id,
                    "log_file": log_file,
                    "message": log.message,
                    "level": log.level,
                    "source": log.source,
                    "platform": log.platform,
                    "position": position + 1,
                    "timestamp": log.timestamp.strftime("%A %b %d, %Y %I:%M %p"),
                    "created_on": log.created_on.strftime("%A %b %d, %Y %I:%M %p"),
                }
            )
        return _logs

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return '<Logged message: {}>'.format(self.message)
