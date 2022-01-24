# app/controllers/__init__.py

"""
This package shall contain the classes containing the logic that manipulates the various tables saved in the database
"""

from .tasks import *
from .sockets import *

app_controllers = {
    TasksController.__name__: TasksController,
    SocketsController.__name__: SocketsController,
}
