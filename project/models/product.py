from typing import Optional
from project.settings import DB_ORM as db


class Product(db.Model):
    '''
        GET ALL PRODUCT IN MENU
    '''
    id = db.Column(db.Integer, primary_key=True)
    # company: str = db.Column(db.String(30))
    # ADD COMPANY ID AND COMPANY TABLE
    uniq_id_product = db.Column(db.Text, unique=True, nullable=False)
    product_name = db.Column(db.Text)
    product_price = db.Column(db.Float)
    id_product_type = db.Column(db.Integer)
    product_type = db.Column(db.Text)
    id_category = db.Column(db.Text)
    category_name = db.Column(db.Text)
    category1 = db.Column(db.Text)
    category2 = db.Column(db.Text)
    tax_name = db.Column(db.Text)
    place_send_name = db.Column(db.Text, nullable=True)
    visible = db.Column(db.Boolean, nullable=False)
    removed = db.Column(db.Boolean, nullable=False)

    @property
    def id_str(self):
        return f"<PRODUCT --> id : {self.uniq_id_product} - name : {self.product_name}>"
