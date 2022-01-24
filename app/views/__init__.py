# app/views/sockets.py

"""
This defines functions that a users directly interact with
"""

from .sockets import Sockets, socketIO

app_views = {
    Sockets.__name__: Sockets,
    "socketIO": socketIO,
}
