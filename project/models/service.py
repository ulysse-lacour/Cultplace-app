import json
from typing import Any, Dict
from datetime import date as date_type
from sqlalchemy.dialects.postgresql import JSONB
from project.settings import DB_ORM as db
from project.models.abstract import SerializableModel


class Service(db.Model, SerializableModel):
    '''
        FIXME when you can this is huge change for production
            Please for all your field names:
                - respect snake_case (no capital)
                - be as specific as you can, you will not be charged at the character
                    - If I need to open this file to understand that "solid" is a number of type float, this is an issue
                    - CA is french nomenclature
                    - Concert is also french
    '''
    id = db.Column(db.Integer, primary_key=True)
    company: str = db.Column(db.String(30))
    # ADD COMPANY ID AND COMPANY TABLE
    date: date_type = db.Column(db.DateTime, nullable=False)
    CA: float = db.Column(db.Float)
    solid: float = db.Column(db.Float)
    liquid: float = db.Column(db.Float)
    majoration: float = db.Column(db.Float)
    graph_url: str = db.Column(db.Text)
    top_liquids = db.Column(JSONB)
    all_products_list_by_name = db.Column(JSONB)
    all_products_timeline = db.Column(JSONB)
    concert: str = db.Column(db.Text)
    concert_infos = db.Column(JSONB)

    non_serializable_fields = {
        'top_liquids',
        'all_products_list_by_name',
        'all_products_timeline',
        'concert_infos',
    }

    @property
    def id_str(self):
        return f"<Service: {self.id} - {self.date}>"
