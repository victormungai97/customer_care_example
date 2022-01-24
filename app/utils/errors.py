# app/utils/errors.py

"""
This module will handle the errors that might arise from the system
It will contain custom functions that redirect user to custom URLs when various errors occur
and a function that logs the errors and informs the admin(s) when said errors occur
"""

import os
import logging
from rq.job import Job
from rq import Queue, Retry
import werkzeug.exceptions as ex
from flask import jsonify
from rq.registry import FailedJobRegistry
from werkzeug.http import HTTP_STATUS_CODES
from logging.handlers import RotatingFileHandler

from app import app

from ..utils import task_config


class BandwidthExceeded(ex.HTTPException):
    """
    Create custom status code for error 509
    """
    code = 509
    description = 'The server is temporarily unable to service your request due to the site owner ' \
                  'reaching his/her bandwidth limit. Please try again later. '


ex.default_exceptions[509] = BandwidthExceeded
HTTP_STATUS_CODES[509] = 'Bandwidth Limit Exceeded'
abort = ex.Aborter()

# change format of log message
# here, we've set the timestamp, logging level, message, source file & line no where log entry originated
LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"


@app.errorhandler(404)
def page_not_found(error):
    errs = str(error).split(':')[-1].split('.')
    print(errs) if app.debug else ""
    return jsonify(error="Page not found"), 404


@app.errorhandler(413)
def too_large(e):
    print(e) if app.debug else ""
    return "File is too large", 413


def set_logger(filename):
    # save info, warnings, errors and critical messages in log file
    # limit size of log file to 1MB(1024*1024 bytes) and keep last 30 log files as backup
    file_handler = RotatingFileHandler(filename, maxBytes=(1024 * 1024), backupCount=30)
    # set format
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # setting logging level to INFO enables logging to cover everything except DEBUG
    file_handler.setLevel(logging.INFO)
    return file_handler


def system_logging(msg, exception=True, log_file='infinite_pay.log'):
    """
    This is a function that handles system error logging,
    from emailing errors to logging the errors in a file.
    The messages in log file will have as much information as possible.
    RotatingFileHandler rotates the logs, ensuring that the log files
    do not grow too large when the application runs for a long time.
    The server writes a line to the logs each time it starts.
    When this application runs on a production server, these log entries will tell you when the server was restarted.
    :param: logs_folder = The folder that will contain the log file
    """
    if exception:
        if app.debug:
            print(msg)
        # Retry up to 3 times, with configurable intervals between retries
        # TODO app.task_queue.enqueue_call(task_config['send_background_error_email'], timeout=3600, retry=Retry(3, 10))

    # Log message to database
    from ..views import Sockets
    Sockets.add_log_message({'level': "exception" if exception else "info", 'message': msg, 'source': "system"})

    # If on an ephemeral system e.g. Heroku, log to stdout
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        # Get and secure the log file
        from werkzeug.utils import secure_filename
        if not log_file or type(log_file) != str:
            log_file = 'infinite_pay.log'
        log_file = secure_filename(log_file)

        # if log folder does not exist, create it
        logs_folder = app.config.get("LOG_FOLDER", "./logs")
        if not os.path.isdir(logs_folder):
            os.makedirs(logs_folder)

        app.logger.addHandler(set_logger(logs_folder + f'/{log_file}'))
        app.logger.setLevel(logging.INFO)
        if exception:
            app.logger.exception(msg)
        else:
            app.logger.info(msg)


def check_failed_rq_jobs(queue_name='find_tasks', delete_job=False):
    """This function will print out jobs that failed to execute on RQ's task queue"""
    queue = Queue(connection=app.redis, name=queue_name)
    registry = FailedJobRegistry(queue=queue)
    # This is how to remove a job from a registry
    for job_id in registry.get_job_ids():
        # Get job whose ID is given
        job = Job.fetch(job_id, connection=app.redis)
        # Print out the job's exception stacktrace
        system_logging(f'\n{job.__dict__["exc_info"]}\n------------------------------------------\n', True, 'redis.log')
        # Remove from registry and delete job
        registry.remove(job_id, delete_job=delete_job)
