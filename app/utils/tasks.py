# app/utils/tasks.py

"""
This module shall contain the various functions that define long running tasks
and that shall require running in a background task queue
"""

import sys
from rq.job import Job
from rq import get_current_job

from ..models import TaskModel, ConversationModel
from ..communication import EmailCommunication
from app import create_app


class BackgroundTaskError(Exception):
    pass


class TaskUtil:
    @staticmethod
    def get_app():
        # Get a Flask application instance and application context
        app = create_app()
        app.app_context().push()
        return app

    @classmethod
    def send_background_error_email(cls):
        EmailCommunication.send_error_email(cls.get_app())

    @classmethod
    def send_background_email(cls, subject, sender, recipients, headers, attachments=None, text_body='', html_body='',
                              sync=True):
        app = cls.get_app()
        try:
            EmailCommunication.send_email(
                subject,
                sender,
                recipients,
                text_body,
                html_body,
                headers,
                attachments=attachments,
                sync=sync,
            )
        except Exception as err:
            app.logger.exception(f'Unhandled exception sending background email\n{err}', exc_info=sys.exc_info())

    @classmethod
    def handle_unhandled_messages(cls):
        app = cls.get_app()
        try:
            job = get_current_job()
            conversations = ConversationModel.query.all()
            for conversation in conversations:
                msg = ConversationModel.retrieve_conversations([conversation])[0]['messages'][-1]
                if msg['is_client']:
                    from ..views import socketIO
                    from ..controllers import SocketsController
                    response = SocketsController.initiate_conversation(msg['message'], msg['conversation_id'])
                    SocketsController.save_message(response, msg['conversation_id'], sender='system')
                    socketIO.emit("received message", {"message": response, "id": msg['conversation_id']})
                    import re
                    if re.search("Thank", response):
                        intro = "Welcome to Infinite Pay support center. How can we be of assistance?"
                        SocketsController.save_message(intro, msg['conversation_id'], sender='system', )
                        socketIO.emit("received message", {"message": intro, "id": msg['conversation_id']})
            # If launched at startup
            if job.meta['startup']:
                from ..controllers import TasksController
                from datetime import datetime, timedelta
                import pytz

                # Cancel any previous repeated task
                repeated_task = TasksController.get_scheduled_task_in_progress('handle_unhandled_messages')
                if repeated_task:
                    result = TasksController.cancel_scheduled_task(repeated_task['id'])
                    if result:
                        app.logger.exception(
                            result if isinstance(result, str) else "Error cancelling repeated tasks",
                            exc_info=(),
                        )

                # Rerun this task periodically
                TasksController.schedule_task(
                    'handle_unhandled_messages',
                    "Handle unanswered messages",
                    # Start this periodic task after a minute delay (in seconds)
                    start=datetime.now(tz=pytz.UTC) + timedelta(seconds=60),  # This time should be in UTC timezone
                    interval=1 * 60,  # Run this periodic task every hour (set in seconds)
                    repeat=None,  # Repeat forever
                    meta={'startup': False},  # Data to be set on meta of task
                )
        except Exception as err:
            app.logger.exception(f'Unhandled exception reacting to unanswered message\n{err}', exc_info=sys.exc_info())

    @staticmethod
    def update_job(job: Job, progress=0.0, message=''):
        job = job if job else get_current_job()
        # Write the percentage and message to the job.meta dictionary and saves it to Redis
        job.meta['progress'] = progress
        job.meta['message'] = message
        job.save_meta()
        # Load the corresponding task object from the database
        task = TaskModel.query.get(job.get_id())
        if task:
            if progress >= 100:
                task.complete = True
            task.save()

    @staticmethod
    def count_words_at_url(url):
        import requests
        resp = requests.get(url)
        print(len(resp.text.split()))


task_config = {
    'send_background_error_email': TaskUtil.send_background_error_email,
    'handle_unhandled_messages': TaskUtil.handle_unhandled_messages,
    'send_background_email': TaskUtil.send_background_email,
    'count_words_at_url': TaskUtil.count_words_at_url,
}
