# app/models/sales.py

from app import db

from . import save, delete, GUID


class SaleModel(db.Model):
    """
    Create a Sales table
    It will store the sales data for credit card machines as from InfinitePay to its clients
    """

    __tablename__ = 'sales'

    id = db.Column(GUID, primary_key=True)
    id_sale = db.Column(db.Integer)
    merchant_id = db.Column(db.Integer)
    chip_id = db.Column(db.Integer)
    created_at = db.Column(db.Text)
    status = db.Column(db.Text)
    description = db.Column(db.Text)

    @staticmethod
    def retrieve_sales(sales: list):
        if not sales or type(sales) != list:
            return []
        _sales = []

        for position, sale in enumerate(sales):
            if not sale or type(sale) != SaleModel:
                continue
            _sales.append({
                'id_sale': sale.id_sale,
                'merchant_id': sale.merchant_id,
                'chip_id': sale.chip_id,
                'created_at': sale.created_at,
                'status': sale.status,
                'description': sale.description,
            })

        return _sales

    def save(self):
        return save(self)

    def delete(self):
        return delete(self)

    def __repr__(self):
        return f"Sale: {self.id}"
