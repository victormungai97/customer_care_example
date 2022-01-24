# app/communication/email.py

"""
This module is for email communication
"""

import logging

from logging.handlers import SMTPHandler
from flask import Flask, current_app
from flask_mail import Message
from threading import Thread
from app import mail


class EmailCommunication:
    """
    This class will support email capabilities
    """

    # this function makes sending email asynchronous(scheduled to run in background)
    # freeing the send_email() to return immediately
    # so that the application can continue running concurrently with the email being sent
    @staticmethod
    def send_async_email(app, msg):
        # The application context that is created with the with app.app_context() call
        # makes the application instance accessible via the current_app variable from Flask.
        with app.app_context():
            mail.send(msg)

    # noinspection PyProtectedMember,PyUnresolvedReferences
    @classmethod
    def send_email(cls, subject, sender, recipients, text_body='', html_body='', headers=None, attachments=None,
                   sync=False):
        """
        This is a helper function that sends email.
        :param subject: Subject of the email
        :param sender: Email address of the sender
        :param recipients: List of email addresses of recipients
        :param text_body: Plain text version of the email
        :param html_body: HTML version of the email
        :param headers: A dictionary of additional headers for the message
        :param attachments: List of tuples consisting of name, media type and data of files to be sent in email
        :param sync: Send the email in the foreground if the email is being sent from background task
        :return: None
        """
        if recipients and type(recipients) == list:
            msg = Message(subject, sender=sender, recipients=recipients)
            if text_body and type(text_body) == str:
                msg.body = text_body
            if html_body and type(html_body) == str:
                msg.html = html_body
            if headers and type(headers) == dict:
                msg.extra_headers = headers
            if attachments and type(attachments) == list:
                for attachment in attachments:
                    # arguments of this method are filename, media type and actual file data
                    # these arguments define an attachment
                    msg.attach(*attachment)
            if sync:
                mail.send(msg)
            else:
                # Here, we start a background thread for email being sent
                # which is much less resource intensive than starting a new process
                Thread(target=cls.send_async_email, args=(current_app._get_current_object(), msg)).start()

    @staticmethod
    def send_error_email(app: Flask):
        """
        Let us email errors to the developers and administrators
        :return: None
        """
        # if app is running without debug mode
        if not app.debug:
            # allow sending logs by email only if mail server has been set
            if app.config.get('MAIL_SERVER'):
                auth = None
                # receive email server credentials, if any
                if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                    auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                secure = None
                # set up secure email traffic transport
                if app.config['MAIL_USE_TLS']:
                    secure = ()
                # SMTPHandler from logging enables sending logs to admins and tech support by email
                recipients = app.config['TECH_MAIL_USERNAME']
                mail_handler = SMTPHandler(
                    mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                    fromaddr=app.config['MAIL_SERVER'],
                    toaddrs=recipients,
                    subject='InfinitePay System Failure',
                    credentials=auth,
                    secure=secure,
                )
                # ensure only errors are reported
                mail_handler.setLevel(logging.ERROR)
                app.logger.addHandler(mail_handler)
