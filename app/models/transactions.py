# app/models/transactions.py

from app import db

from . import save, delete, GUID


class TransactionModel(db.Model):
    """
    Create a Transaction table
    This table shows transaction data which went through InfinitePay's credit card machines
    """

    __tablename__ = 'transactions'

    id = db.Column(GUID, primary_key=True)
    transaction_id = db.Column(db.Integer)
    merchant_id = db.Column(db.Integer)
    created_at = db.Column(db.Text)
    value = db.Column(db.Float)

    @staticmethod
    def retrieve_transactions(transactions: list):
        if not transactions or type(transactions) != list:
            return []
        _transactions = []

        for position, transaction in enumerate(transactions):
            if not transaction or type(transaction) != TransactionModel:
                continue
            _transactions.append({
                'transaction_id': transaction.transaction_id,
                'merchant_id': transaction.merchant_id,
                'created_at': transaction.created_at,
                'value': transaction.value,
            })

        return _transactions

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return f"Transaction: {self.id}"
