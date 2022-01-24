# app/controllers/tasks.py

import rq
import uuid

from datetime import datetime
from flask import current_app

from ..models import TaskModel, ScheduledTaskModel
from ..utils import task_config, system_logging, TaskUtil

APP = current_app


def report_success(job, connection, result, *args, **kwargs):
    app = TaskUtil.get_app()
    # Load the corresponding task object from the database
    task = TaskModel.query.get(job.get_id())
    if not task:
        task = ScheduledTaskModel.query.get(job.get_id())
    message = f'''Success!{f' {(task.description or "Job").capitalize()} completed.' if task else ""}'''
    progress = 100 if result is None or type(result) != dict else result.get('progress', 100) or 100
    if message.capitalize().startswith('Err'):
        return report_failure(job, connection)
    msg = message if result is None or type(result) != dict else result.get('message', message) or message
    TaskUtil.update_job(job, progress if type(progress) == int else 100, msg if type(msg) == str else message)
    app.logger.info(f'{message}\nArgs: {args}\tKwargs: {kwargs}')


def report_failure(job, _, _type=None, value=None, traceback=None):
    app = TaskUtil.get_app()
    # Load the corresponding task object from the database
    task = TaskModel.query.get(job.get_id())
    if not task:
        task = ScheduledTaskModel.query.get(job.get_id())
    description = task.description or "job" if task else "job"
    message = f'Unhandled exception{f" running {description}"}\nRQ Job {job} on connection {_}'
    TaskUtil.update_job(job, 100, message)
    app.logger.exception(message, exc_info=(_type, value, traceback))


class TasksController:
    """
    This class contains the logic surrounding background tasks
    """

    @classmethod
    def launch_task(cls, name, description, meta=None, *args, **kwargs):
        """
        Submit task to RQ queue
        :param name: Task/function name as defined in app/tasks.py
        :param description: Friendly description of the task that can be presented to users
        :param meta: Arbitrary pickle-able data on the job itself
        :param args: Positional arguments to be passed to the task
        :param kwargs: Keyword arguments that will be passed to the task
        """
        try:
            if not name or type(name) != str:
                system_logging("Task function provided", exception=True)
                return None
            if name not in task_config:
                system_logging("Non-existent Task function provided", exception=True)
                return None

            from rq import Retry
            # Submit the job and add it to the queue
            fn = task_config[name]
            # Retry up to 3 times, with configurable intervals between retries
            job = APP.task_queue.enqueue(
                fn, args=args, kwargs=kwargs, job_timeout=30, retry=Retry(3, [10, 30, 60]),
                on_success=report_success, on_failure=report_failure,
                meta=meta if meta and type(meta) == dict else {},
            )
            if not job:
                system_logging("Job has not been queued", exception=True)
                return None
            # Create a corresponding Task object in database based on RQ-assigned task ID
            task = TaskModel(id=job.get_id(), name=name, description=description)
            # Add the new task object to the session, but it does not issue a commit
            status = task.save()
            if status:
                system_logging('Unable to queue task', exception=True)
            return task
        except BaseException as err:
            system_logging(err)
            return None

    @staticmethod
    def get_tasks_in_progress():
        """Return the complete list of tasks that are outstanding"""
        try:
            tasks = TaskModel.query.filter_by(complete=False).all()
            if not tasks:
                return None

            return TaskModel.retrieve_tasks(tasks)
        except BaseException as err:
            system_logging(err)
            return None

    @staticmethod
    def get_task_in_progress(name):
        """
        Return a specific outstanding task.
        Prevent user from starting two or more tasks of the same type concurrently,
        Therefore, check if a previous task is currently running before launching a task
        """
        try:
            task = TaskModel.query.filter_by(name=name, complete=False).first()
            if not task:
                return None

            return TaskModel.retrieve_tasks([task])[0]
        except BaseException as err:
            system_logging(err)
            return None

    @classmethod
    def cancel_task(cls, job):
        """
        Given a job, check if it is in task queue and cancel it if true
        :param job: RQ Job or Job ID
        :return: None
        """
        try:
            job = "" if not job else job if type(job) == str else job.get_id() if type(job) == rq.job.Job else ""
            task = TaskModel.query.filter(TaskModel.id == job).first()
            if not task:
                return 'No such task'
            task_queue = APP.task_queue
            if task.id in task_queue.job_ids:
                cls.get_rq_job(task.id).cancel()
                task.complete = True
                return task.save()
            return None
        except BaseException as err:
            system_logging(err, exception=True)
            return 'Unable to complete task'

    @staticmethod
    def get_rq_job(task_id) -> rq.job.Job or None:
        """
        Helper method that loads the RQ Job instance, from a given task id,
        :return: The RQ Job instance or None in case of error
        """
        try:
            # Loads the Job instance from the data that exists in Redis about it
            return rq.job.Job.fetch(task_id, connection=APP.redis) if task_id else None
        except BaseException as err:
            system_logging(err)
            return None

    @classmethod
    def get_progress(cls, task: TaskModel):
        """
        Builds on top of get_rq_job().
        Assumptions:
            1. If the job id from the model does not exist in the RQ queue, that means that the job already finished and
                the data expired and was removed from the queue, so in that case the percentage returned is 100
            2. If the job exists, but there is no information associated with the meta attribute, then it is safe to
                assume that the job is scheduled to run, but did not get a chance to start yet,
                so in that situation, 0 is returned as progress
        :return: Progress percentage for the task
        """
        job = cls.get_rq_job(task.id if task else None)
        return job.meta.get('progress', 0) if job is not None else 100

    @staticmethod
    def schedule_task(name, description, start, interval, repeat=None, meta=None, *args, **kwarg):
        """
        Schedule task using RQ Scheduler and add it to the database
        :param name: Name of task/function to be queued as defined in app/tasks.py
        :param description: Friendly description of the task that can be presented to users
        :param start: Time for first execution, in UTC timezone
        :param interval: Time before the function is called again, in seconds
        :param repeat: Repeat this number of times (None means repeat forever)
        :param meta: Arbitrary pickle-able data on the job itself
        :param args: Positional arguments to be passed to the task when executed
        :param kwarg: Keyword arguments that will be passed to the task when executed
        :return: The task itself
        """
        try:
            if not name or type(name) != str:
                system_logging("Task function provided", exception=True)
                return None
            if name not in task_config:
                system_logging("Non-existent Task function provided", exception=True)
                return None

            start = start if start and type(start) == datetime else datetime.utcnow()
            interval = interval if interval and type(interval) == int else 60
            repeat = repeat if repeat is None or type(repeat) == int else 10
            meta = meta if meta and type(meta) == dict else {}

            # Submit the job and add it to the queue
            rq_job = APP.scheduler.schedule(
                scheduled_time=start,
                func=task_config[name],
                args=args,
                kwargs=kwarg,
                interval=interval,
                repeat=repeat,
                meta=meta,
                on_success=report_success,
                on_failure=report_failure,
            )
            if not rq_job:
                system_logging("Job has not been scheduled", exception=True)
                return None
            # Create a corresponding Task object in database based on RQ-assigned task ID
            scheduled_task = ScheduledTaskModel(
                id=rq_job.get_id(), name=name, start=start, interval=interval, description=description
            )
            # Add the new task object to the session, but it does not issue a commit
            status = scheduled_task.save()
            if status:
                system_logging('Unable to start scheduled task', exception=True)
            return scheduled_task
        except BaseException as err:
            system_logging(err)
            return None

    @staticmethod
    def get_scheduled_tasks_in_progress():
        """Return the complete list of scheduled tasks that are outstanding"""
        try:
            scheduled_tasks = ScheduledTaskModel.query.filter_by(cancelled=False).all()
            if not scheduled_tasks:
                return None

            return ScheduledTaskModel.retrieve_scheduled_tasks(scheduled_tasks)
        except BaseException as err:
            system_logging(err)
            return None

    @staticmethod
    def get_scheduled_task_in_progress(name):
        """
        Return a specific outstanding task.
        Prevent user from starting two or more tasks of the same type concurrently,
        Therefore, check if a previous task is currently running before launching a task
        """
        try:
            if not name or not isinstance(name, str):
                return None

            scheduled_task = ScheduledTaskModel.query.filter_by(name=name, cancelled=False).first()
            if not scheduled_task:
                return None

            return ScheduledTaskModel.retrieve_scheduled_tasks([scheduled_task])[0]
        except BaseException as err:
            system_logging(err)
            return None

    @staticmethod
    def cancel_scheduled_task(job):
        """
        Given a job, check if it is in scheduler and cancel it if true
        :param job: RQ Job or Job ID
        :return: None
        """
        try:
            if not isinstance(job, uuid.UUID):
                task_id = uuid.UUID(
                    "" if not job else job if type(job) == str else job.get_id() if type(job) == rq.job.Job else ""
                )
            else:
                task_id = job
            scheduled_task = ScheduledTaskModel.query.filter(ScheduledTaskModel.id == task_id).first()
            if not scheduled_task:
                return 'No such scheduled task'
            scheduler = APP.scheduler
            types = (bytes, str, int, float, rq.job.Job)
            j = job if isinstance(job, types) else job.hex if isinstance(job, uuid.UUID) else ""
            if j in scheduler:
                scheduler.cancel(job)
                scheduled_task.cancelled = True
                return scheduled_task.save()
            return None
        except BaseException as err:
            system_logging(err, exception=True)
            return 'Unable to cancel scheduled task'
