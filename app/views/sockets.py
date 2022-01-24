# app/views/sockets.py

import sys
import pytz
import uuid

from datetime import datetime
from flask_socketio import SocketIO

from app import app

from ..utils import Helper
from ..models import LogModel
from ..controllers import SocketsController

REDIS_URL = Helper.generate_redis_url()

# Start SocketIO server, allow CORS and connect to a message queue e.g. Redis
socketIO = SocketIO(app, cors_allowed_origins="*", message_queue=REDIS_URL if type(REDIS_URL) == str else 'redis://')


class Sockets:

    @staticmethod
    @socketIO.on('setup')
    def setup(data):
        conversation = SocketsController.retrieve_conversation(data.get('id'))
        if not conversation:
            messages = [
                {
                    "message": 'Welcome to Infinite Pay support center. How can we be of assistance?',
                    "is_client": False
                },
            ]
        else:
            from ..models import ConversationModel
            messages = ConversationModel.retrieve_conversations([conversation])[0]['messages']
        socketIO.emit('setup complete', dict(messages=messages, id=data.get('id')))

    @staticmethod
    @socketIO.on('add message')
    def add_message(data):
        uid = data.get('id')
        message = data.get('message')
        channel = 'received message'
        if not message or not isinstance(message, str):
            socketIO.emit(channel, dict(message='Please enter your message', id=uid))
            return
        response = SocketsController.initiate_conversation(message, uid)
        SocketsController.save_message(response, uid, sender='system')
        socketIO.emit(channel, {"message": response, "id": uid})
        import re
        if re.search("Thank", response):
            intro = "Welcome to Infinite Pay support center. How can we be of assistance?"
            SocketsController.save_message(intro, uid, sender='system', )
            socketIO.emit(channel, {"message": intro, "id": uid})

    @staticmethod
    @socketIO.on('my_ping')
    def my_ping():
        socketIO.emit('my_pong')

    @staticmethod
    @socketIO.on('add log')
    def add_log_message(data):
        """Add a log message"""
        try:
            if not data.get('timestamp') or type(data.get('timestamp')) is not str:
                timestamp = datetime.now(tz=pytz.timezone('Africa/Nairobi'))
            else:
                timestamp = datetime.strptime(data.get('timestamp'), "%A %b %d, %Y %I:%M %p")

            stack_trace = data.get('stackTrace')
            level = data.get('level') or "info"
            filename = None
            if stack_trace:
                import os
                import logging

                # Create a custom logger
                logger = logging.getLogger(__name__)

                # if log folder does not exist, create it
                log_folder = f'{app.config.get("UPLOAD_FOLDER", "./uploads") or "./uploads"}/flutter/{level}'
                if not os.path.isdir(log_folder):
                    os.makedirs(log_folder)

                # Create handlers
                filename = f'{log_folder}/error_{timestamp.strftime("%Y_%m_%d")}.log'
                f_handler = logging.FileHandler(filename=filename)

                # Create formatters
                f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

                # Add formatter to handlers
                f_handler.setFormatter(f_format)

                # Add handlers to the logger
                logger.addHandler(f_handler)

                # Log stack trace
                logger.error(
                    f"{data.get('message')} from {data.get('source')} on platform {data.get('platform')}\n{stack_trace}"
                )

            status = LogModel(
                id=uuid.uuid4(),
                message=data.get('message') or "",
                source=data.get('source') or "",
                platform=data.get('platform'),
                timestamp=timestamp,
                log_file=filename,
                level=level,
            ).save()
            if status:
                app.logger.exception(f'Error Problem adding log message', exc_info=())
        except Exception as err:
            app.logger.exception(f'Unhandled exception adding log message\n{err}', exc_info=sys.exc_info())
