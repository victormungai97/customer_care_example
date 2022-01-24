# app/models/conversations.py

from app import db

from . import save, delete, time_now


class ConversationModel(db.Model):
    """
    Create a Conversation table
    All conversations (i.e. all people who contact customer support) can be kept here for future reference
    """

    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.String(50), nullable=False, unique=True)
    creation_date = db.Column(db.DateTime, default=time_now(), )
    # Relationship between conversations and messages
    messages = db.relationship(
        'MessageModel',
        primaryjoin='MessageModel.conversation_id == ConversationModel.conversation_id',
        backref='messages', lazy='dynamic',
    )

    @staticmethod
    def retrieve_conversations(conversations):
        if not conversations or not isinstance(conversations, list):
            return []
        _conversations = []
        for conversation in conversations:
            if not conversation or not isinstance(conversation, ConversationModel):
                continue
            messages = MessageModel.query.filter(MessageModel.conversation_id == conversation.conversation_id).all()
            _conversations.append({
                'id': conversation.conversation_id,
                'messages': MessageModel.retrieve_messages(messages),
                'creation_date': conversation.creation_date.strftime("%A %b %d, %Y %I:%M %p"),
            })
        return _conversations

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return '<Conversation {}>'.format(self.conversation_id)


class MessageModel(db.Model):
    """
    Create a Message table
    This will hold the communication(messages) between client and chatbot
    """

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        db.String(50),
        db.ForeignKey('conversations.conversation_id', ondelete='CASCADE', onupdate='CASCADE'),
    )
    body = db.Column(db.Text)
    sender = db.Column(db.Text, default='client')
    timestamp = db.Column(db.DateTime, default=time_now(), )

    @staticmethod
    def retrieve_messages(messages):
        if not messages or not isinstance(messages, list):
            return []
        _messages = []
        for message in messages:
            if not message or not isinstance(message, MessageModel):
                continue
            _messages.append({
                'id': message.id,
                'timestamp': message.timestamp.strftime("%A %b %d, %Y %I:%M %p"),
                'sender': message.sender,
                'is_client': message.sender == 'client',
                'conversation_id': message.conversation_id,
                'message': message.body,
            })
        return _messages

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
