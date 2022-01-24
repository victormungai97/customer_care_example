# app/models/receipts.py

from app import db

from . import save, delete, GUID


class ReceiptModel(db.Model):
    """
    Create a Receipt table
    Keep track of value transfer data to an InfinitePay customer's bank account arising from transactions
    """
    __tablename__ = 'receipts'

    id = db.Column(GUID, primary_key=True)
    merchant_id = db.Column(db.Integer)
    created_at = db.Column(db.Text)
    status = db.Column(db.Text)
    description = db.Column(db.Text)
    value = db.Column(db.Float)

    @staticmethod
    def retrieve_receipts(receipts: list):
        if not receipts or type(receipts) != list:
            return []
        _receipts = []
        for position, receipt in enumerate(receipts):
            if not receipt or type(receipt) != ReceiptModel:
                continue
            _receipts.append({
                'merchant_id': receipt.merchant_id,
                'created_at': receipt.created_at,
                'status': receipt.status,
                'description': receipt.description,
                'value': receipt.value,
            })
        return _receipts

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return f"Receipt: {self.id}"
