# app/models/tags.py

from app import db

from . import save, delete, time_now, GUID


class ActionModel(db.Model):
    """
    Create an Action table
    For every ongoing conversation, we shall tag what action that the conversation is based on
    This will then enable the bot to keep track of the conversation and know what to do
    """

    __tablename__ = 'actions'

    id = db.Column(GUID, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=time_now())
    conversation_id = db.Column(db.Text, nullable=False)

    @staticmethod
    def retrieve_actions(actions: list):
        if not actions or type(actions) != list:
            return []
        _actions = []
        for position, action in enumerate(actions):
            if not action or not isinstance(action, ActionModel):
                continue
            _actions.append({
                'position': position + 1,
                'id': action.id,
                'name': action.name,
                'completed': action.completed,
                'conversation_id': action.conversation_id,
                'timestamp': action.timestamp.strftime("%A %b %d, %Y %I:%M %p"),
            })

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return f'Action: {self.id}'
