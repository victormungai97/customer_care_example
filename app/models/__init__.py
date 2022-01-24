# app/models/__init__.py

"""
This package shall contain the various classes to be mapped to SQL tables and their associated helper functions
"""

import sys
import uuid

import pytz

from app import db, app


def time_now():
    """
    Here, we shall the current time in Kenya's timezone
    :return: The current datetime in Kenyan time
    """
    import datetime
    return datetime.datetime.now(tz=pytz.timezone('Africa/Nairobi'))


def save(field: db.Model):
    """
    Method to save a field into the database
    If successful, the field is committed and success status code returned
    If unsuccessful, the field is rolled back and failure status code returned
    :param field: The record to be saved
    :return: Status code. 0 -> Success, 1 -> Failure
    """
    try:
        db.session.add(field)
        db.session.commit()
        return 0
    except Exception as err:
        app.logger.exception(f'Error saving field {field}\nException: {err}', exc_info=sys.exc_info())
        db.session.rollback()
        return 1


def delete(field):
    """
    Method to delete a field from the database
    If successful, the field is committed and success status code returned
    If unsuccessful, the field is rolled back and failure status code returned
    :param field: The record to be saved
    :return: Status code. 0 -> Success, 1 -> Failure
    """
    try:
        db.session.delete(field)
        db.session.commit()
        return 0
    except Exception as err:
        app.logger.exception(f'Error deleting field {field}\nException: {err}', exc_info=sys.exc_info())
        db.session.rollback()
        return 1


def delete_file(path):
    """
    Method to delete a file from file system during deletion of a field
    :param path: Relative URL to file from root static folder
    """
    try:
        import os
        from urllib.parse import urlparse
        if path and not urlparse(path).scheme:
            filename = os.path.abspath(f'{os.getcwd()}/app/{path}')
            if os.path.isfile(filename):
                # Delete the file
                os.remove(filename)
    except Exception as err:
        app.logger.exception(f'Error deleting file {path}\nException: {err}', exc_info=sys.exc_info())


class GUID(db.TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    String(32), storing as stringified hex values.

    """
    impl = db.String(length=50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


from .tasks import TaskModel
from .scheduled_tasks import ScheduledTaskModel
from .logs import LogModel
from .receipts import ReceiptModel
from .sales import SaleModel
from .transactions import TransactionModel
from .actions import ActionModel
from .conversations import ConversationModel, MessageModel

app_models = {
    'db': db,
    TaskModel.__name__: TaskModel,
    ScheduledTaskModel.__name__: ScheduledTaskModel,
    LogModel.__name__: LogModel,
    ActionModel.__name__: ActionModel,
    ConversationModel.__name__: ConversationModel,
    MessageModel.__name__: MessageModel,
}
