# app/controllers/sockets.py

"""
This module will contain methods that implement logic for the conversation
"""

import re
import uuid
import requests

from ..utils import system_logging
from ..models import ConversationModel, MessageModel, ActionModel, SaleModel, TransactionModel, ReceiptModel


class SocketsController:
    LOGISTICS_URL = "https://logistics-api-dot-active-thunder-329100.rj.r.appspot.com"
    TELECOMS_URL = "https://telecom-api-dot-active-thunder-329100.rj.r.appspot.com"

    KEYWORDS = {
        "receipt": {"account", "bank", "receipt"},
        "chip_status": {"chip", "machine"},
        "zip_code": {"zip", "address", "home"},
        "sales": {"sale"},
        "transactions": {'transaction'},
        "tracking": {"track"},
    }

    IDS = {
        "tracking": 'Sale ID',
        "zip_code": 'Zip Code',
        "chip_status": 'Chip ID',
        "sales": "Sale ID",
        "transactions": 'Transaction ID',
        "receipt": 'Merchant ID',
    }

    TABLES = {
        "sales": SaleModel,
        "transactions": TransactionModel,
        "receipt": ReceiptModel,
    }

    APIS = {
        "tracking": 'tracking',
        "zip_code": 'zip_code',
        "chip_status": 'chip_status',
    }

    @staticmethod
    def retrieve_conversation(conversation_id):
        if not conversation_id or not isinstance(conversation_id, str):
            return None

        conversation = ConversationModel.query.filter(ConversationModel.conversation_id == conversation_id).first()
        if not conversation:
            conversation = ConversationModel(conversation_id=conversation_id)
            if conversation.save():
                system_logging('Error creating conversation. Please review', exception=True)
                return None
            first_message = 'Welcome to Infinite Pay support center. How can we be of assistance?'
            MessageModel(conversation_id=conversation_id, body=first_message, sender='system').save()

        return conversation

    @classmethod
    def save_message(cls, message: str, uid: str, sender: str = None):
        if not cls.retrieve_conversation(uid):
            return 'Unable to continue. Please refresh page'
        _message = MessageModel()
        _message.conversation_id = uid
        _message.body = message if message or type(message) == str else ''
        _message.sender = sender if sender or type(sender) == str else 'client'
        if _message.save():
            system_logging('Error saving message. Please review', exception=True)
            return 'Unable to continue. Please refresh page'
        return None

    @classmethod
    def initiate_conversation(cls, message, uid, is_saved: bool = False):
        if not is_saved:
            msg = cls.save_message(message, uid)
            if msg:
                return msg
        action = ActionModel.query.filter_by(conversation_id=uid, completed=False).first()
        if not action:
            return cls.respond_message(message, uid)
        else:
            name, response = action.name, None
            if name in cls.APIS:
                response = cls.request_api(name, message)
            elif name in cls.TABLES:
                response = cls.request_database(name, message)
            if not response:
                return f"Oops!! We fear that you may have entered incorrect identifier\nCarefully re-enter correct {cls.IDS[name]}\n"
            else:
                action.completed = True
                if not action.save():
                    return f"{response}\nThank you for your reaching out and reach out to us when you have an issue"
            return f"Please provide your {cls.IDS[name]}"

    @classmethod
    def respond_message(cls, message, uid):
        # This marks a new phase of the conversation
        keyword = None
        # Look for keywords
        for action, keywords in cls.KEYWORDS.items():
            for word in keywords:
                if re.search(word, message):
                    keyword = action
                    break
        # If not keyword found, show them list of options
        if not keyword:
            message = 'For better service delivery, please an option from the following options\n'
            for i, key in enumerate(cls.KEYWORDS):
                message = f'{message}\n{key.replace("_", " ").title()}'
        else:
            ActionModel(id=uuid.uuid4(), conversation_id=uid, name=keyword).save()
            message = f"Please provide your {cls.IDS[keyword]}"
        return message

    @classmethod
    def request_api(cls, name, identifier):
        url, body = None, {}
        keys = list(cls.APIS.keys())
        if name == keys[0]:
            url = f'{cls.LOGISTICS_URL}/{cls.APIS[name]}'
            body = {"id_sale": identifier}
        elif name == keys[1]:
            url = f'{cls.LOGISTICS_URL}/{cls.APIS[name]}'
            body = {"zip_code": identifier}
        elif name == keys[2]:
            url = f'{cls.TELECOMS_URL}/{cls.APIS[name]}'
            body = {"chip_id": identifier}
        return cls.retrieve_api(url, body=body, action=name)

    @classmethod
    def request_database(cls, name, id_: str):
        keys = list(cls.TABLES.keys())
        if not id_.isnumeric():
            return None
        if name == keys[0]:
            results = cls.TABLES[name].retrieve_sales(cls.TABLES[name].query.filter_by(id_sale=id_).all())
        elif name == keys[1]:
            results = cls.TABLES[name].retrieve_transactions(cls.TABLES[name].query.filter_by(transaction_id=id_).all())
        elif name == keys[2]:
            results = cls.TABLES[name].retrieve_receipts(cls.TABLES[name].query.filter_by(merchant_id=id_).all())
        else:
            results = []
        if not results:
            return None
        message = f"The following result was found for your {name} query\n"
        for position, res in enumerate(results):
            message += f'\n<b>Result: {position + 1}</b>\n\n'
            message += "\n".join(
                f'{key.replace("_", " ").title()}: {value}\n' for key, value in res.items() if value
            )
        return message

    @classmethod
    def retrieve_api(cls, url: str, body: dict, action='') -> dict or None:
        if not url or not isinstance(url, str):
            return None

        if not body or not isinstance(body, dict):
            return None

        response = requests.post(url, data=body, headers={'authorization': 'teste'})
        if not response:
            system_logging(f"{url} RESPONSE: {response.text}\nSTATUS CODE: {response.status_code}", exception=True)
            return None

        result = response.json()
        keys = list(cls.APIS.keys())
        if action == keys[0]:
            return "The products is {} with a delivery forecast for {} to be delivered to Zip Code {}".format(
                result['status'], result['delivery_forecast'], result['destination_zip_code']
            )
        elif action == keys[2]:
            return f"Chip with ID {result['CHIP37648']} is {result['status']}.\nMessage is \'{result['description']}\'"
        else:
            return "\n".join(f'{key.replace("_", " ").title()}: {value}' for key, value in result.items() if value)
