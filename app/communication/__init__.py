# app/communication/__init__.py

"""
This package contains the modules needed for various communication mechanisms
"""

from .email import *
from .messages import *

app_communication = {
    Messages.__name__: Messages,
    EmailCommunication.__name__: EmailCommunication,
}
