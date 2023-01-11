# synchers.py

import logging
from datetime import datetime
from typing import Any, Collection, Dict, List, Mapping, Optional, Set, Tuple, Union

import requests
from requests import HTTPError
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from sqlalchemy import inspect
from werkzeug.exceptions import Conflict, HTTPException, NotFound

from project.models.product import Product
from project.settings import (
    APP_NAME,
    DB_ORM,
    LADDITION_AUTH_TOKEN,
    LADDITION_CUSTOMER_ID,
    SOWPROG_EMAIL_CREDENTIAL,
    SOWPROG_PASSWORD
)

SOWPROG_URL = "https://agenda.sowprog.com/rest/v1_2/scheduledEventsSplitByDate/search?"

logger = logging.getLogger(APP_NAME)

# --------------- #
# CONCERT SYNCHER #
# --------------- #


def get_concert_infos_from_sowprog_api_with_date(date_to_search: datetime) -> Mapping[str, Any]:
    headers: CaseInsensitiveDict = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    auth_object = HTTPBasicAuth(
        SOWPROG_EMAIL_CREDENTIAL,
        SOWPROG_PASSWORD,
    )

    sowprog_params = (
        ('eventScheduleDate.date', '{}'.format(date_to_search.strftime('%Y-%m-%d'))),
        ('past_events', 'True'),
    )

    # REQUETE API POUR SOWPROG
    sowprog_reponse = requests.get(
        SOWPROG_URL,
        auth=auth_object,
        headers=headers,
        params=sowprog_params
    )

    sowprog_reponse.raise_for_status()

    sowprog_raw_data: Mapping[str, Any] = sowprog_reponse.json()

    return sowprog_raw_data


def unpack_and_check_sowprog_data(sowprog_raw_data: Mapping[str, Any]) -> Tuple[
        str,  # concert_name
        Dict[str, Any],  # concert_infos
        Optional[HTTPException]  # error
]:
    sowprog_infos = sowprog_raw_data.get("eventDescriptionSplitByDate", None)
    if (
        sowprog_infos is not None
        and len(sowprog_infos) == 1
    ):
        [sowprog_info] = sowprog_infos
        sowprog_title = sowprog_info['event']['title']
        sowprog_free = sowprog_info['freeAdmission']
        sowprog_style = sowprog_info['event']['eventStyle']['label']
        sowprog_fb = '#'
        if 'facebookFanPage' in sowprog_info['event']:
            sowprog_fb = sowprog_info['event']['facebookFanPage']
        sowprog_picture = '#'
        if 'picture' in sowprog_info['event']:
            sowprog_picture = sowprog_info['event']['picture']
        concert_name = sowprog_title
        concert_infos = {
            'title': sowprog_title,
            'facebook': sowprog_fb,
            'style': sowprog_style,
            'free': sowprog_free,
            'picture': sowprog_picture,
        }
        return concert_name, concert_infos, None
    else:
        # default without concert infos
        concert_infos = {
            'title': 'Sans concert',
            'facebook': '#',
            'style': '',
            'free': 'true',
            'picture': '#',
        }
        if sowprog_infos is None:
            concert_name = 'Error with API'
            return concert_name, concert_infos, NotFound(
                description="SowProgAPI failed to provide data"
            )
        elif len(sowprog_infos) > 1:
            concert_name = 'Multiples concerts'
            logger.warning(
                msg="Failed to parse sowprog response",
                extra={
                    "sowprog_infos": sowprog_infos,
                }
            )
            return concert_name, concert_infos, Conflict(
                description="Too many data from SowProgAPI"
            )
        else:
            concert_name = 'Sans concert'
            return concert_name, concert_infos, None


def sowprog_syncher(date_to_search: datetime) -> Tuple[
        str,  # concert_name
        Dict[str, Any],  # concert_infos
        Optional[HTTPException]  # error
]:
    sowprog_raw_data = get_concert_infos_from_sowprog_api_with_date(date_to_search)
    return unpack_and_check_sowprog_data(sowprog_raw_data)

# --------------- #
# PRODUCT SYNCHER #
# --------------- #


class ProductSyncher:
    menu_url = "https://api.laddition.com/dimproduct"
    product_column_names = {
        column.key
        for column in inspect(Product).attrs
    }

    @classmethod
    def sync_products(cls) -> Tuple[
        List[Product],  # Product added
        List[Product],  # Product updated
    ]:
        """
        Grab remote data from laddition API, and create_or_update first party products.
        """

        new_products = cls.get_remote_products()

        new_products_third_party_ids = {
            product.uniq_id_product
            for product in new_products
        }

        existing_products = Product.query.filter(
            Product.uniq_id_product.in_(new_products_third_party_ids)
        ).all()

        updated_products, remaining_products_to_create = cls.batch_update_products_from_products(
            first_party_products=existing_products,
            third_party_products=new_products,
        )

        cls.batch_save_products(
            products_to_save=remaining_products_to_create,
        )

        logger.info(
            msg=f"Created {len(remaining_products_to_create)} new products",
            extra={
                "created_product_ids": [product.id for product in remaining_products_to_create]
            }
        )

        return (
            remaining_products_to_create,
            updated_products,
        )

    @classmethod
    def get_remote_products(cls) -> List[Product]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {LADDITION_AUTH_TOKEN}",
            "customerid": LADDITION_CUSTOMER_ID,
        }

        products_response = requests.get(
            cls.menu_url,
            headers=headers  # type: ignore
        )

        products_response.raise_for_status()

        products_data = products_response.json()

        last_page_index = products_data["lastPage"]

        detailed_products_data: List[Dict[str, Any]] = []
        for page_index in range(1, last_page_index + 1):
            product_page_response = requests.get(
                f"{cls.menu_url}?page={page_index}",
                headers=headers  # type: ignore
            )
            try:
                product_page_response.raise_for_status()
            except HTTPError as exc:
                logger.exception(
                    msg=f"Failed to load page {page_index} due to network error",
                    exc_info=exc
                )
                continue

            detailed_products_data.extend(product_page_response.json()["data"])

        return ProductSyncher._extract_products_from_remote_data(detailed_products_data)

    @classmethod
    def batch_update_products_from_products(
        cls,
        first_party_products: List[Product],
        third_party_products: List[Product],
    ) -> Tuple[
        List[Product],  # updated first party products
        List[Product],  # Third party products whose data were not written into db
    ]:
        """
        Find differences between existing first party products and remote third party products.
        Return a list of product updated and a list of remaining third_party_products (potentially to
        save later)
        """
        third_party_id_to_third_party_product = {
            product.uniq_id_product: product
            for product in third_party_products
        }

        products_to_update: Set[Product] = set()

        for product in first_party_products:
            matching_product = third_party_id_to_third_party_product[product.uniq_id_product]

            diff_mapping = cls._compare_products(
                old_product=product,
                new_product=matching_product,
            )

            if diff_mapping is not None:
                for column, value in diff_mapping.items():
                    setattr(
                        product,
                        column,
                        value,
                    )
                products_to_update.add(product)

            third_party_products.remove(matching_product)

        cls.batch_save_products(
            products_to_save=products_to_update
        )

        logger.info(
            msg=f"Updated {len(products_to_update)} existing products",
            extra={
                "updated_product_ids": [product.id for product in products_to_update]
            }
        )

        return (
            list(products_to_update),
            third_party_products,
        )

    @classmethod
    def batch_save_products(
        cls,
        products_to_save: Collection[Product]
    ) -> None:
        if len(products_to_save) > 0:
            DB_ORM.session.bulk_save_objects(products_to_save)
            DB_ORM.session.commit()

    @classmethod
    def _compare_products(
        cls,
        old_product: Product,
        new_product: Product,
    ) -> Optional[Dict[str, Any]]:

        diff: Dict[str, Any] = {}

        for column_name in cls.product_column_names:
            if column_name == "id":
                continue

            old_column_value = getattr(old_product, column_name)
            new_column_value = getattr(new_product, column_name)

            if new_column_value != old_column_value:
                diff.setdefault(
                    column_name,
                    new_column_value
                )
        if len(diff) > 0:
            return diff
        else:
            return None

    @staticmethod
    def _extract_products_from_remote_data(
        products_data: List[Dict[str, Any]],
    ) -> List[Product]:
        return [
            Product(
                uniq_id_product=str(product['id_product_global']),
                product_name=product['product_name'],
                product_price=float(product['product_price']),
                id_product_type=int(product['id_product_type']),
                product_type=product['product_type'],
                id_category=product['id_category'],
                category_name=product['category_name'],
                category1=product['category1'],
                category2=product['category2'],
                tax_name=product['tax_name'],
                place_send_name=product['place_send_name'],
                visible=bool(product['visible']),
                removed=bool(product['removed']),
            )
            for product in products_data
            if product['id_product_global'] is not None
        ]
