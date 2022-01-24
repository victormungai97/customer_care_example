# app/utils/__init__.py

"""
This package shall bring together the various utility modules and functions required in various parts of the app
"""

from .misc import *
from .tasks import *
from .errors import *

roles = ['admin', 'client', 'provider']

app_utils = {
    TaskUtil.__name__: TaskUtil,
    Helper.__name__: Helper,
    BandwidthExceeded.__name__: BandwidthExceeded,
    BackgroundTaskError.__name__: BackgroundTaskError,
    'set_logger': set_logger,
    'task_config': task_config,
    'system_logging': system_logging,
    'check_failed_rq_jobs': check_failed_rq_jobs,
}
