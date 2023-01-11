from datetime import datetime
from unittest.mock import MagicMock, NonCallableMagicMock, call, patch

import pytest
from project.models.product import Product
from project.settings import (
    DB_ORM,
    LADDITION_AUTH_TOKEN,
    LADDITION_CUSTOMER_ID,
    SOWPROG_EMAIL_CREDENTIAL,
    SOWPROG_PASSWORD
)
from project.synchers import (
    SOWPROG_URL,
    ProductSyncher,
    get_concert_infos_from_sowprog_api_with_date,
    unpack_and_check_sowprog_data
)
from requests import HTTPError
from werkzeug.exceptions import Conflict, NotFound

# --------------------- #
# Concert Syncher tests #
# --------------------- #


@patch("project.synchers.requests")
@patch("project.synchers.HTTPBasicAuth")
def test_get_concert_infos_from_sowprog_api_with_date_success(
    mocked_http_basic_auth: NonCallableMagicMock,
    mocked_requests: NonCallableMagicMock,
):
    mocked_http_basic_auth.return_value = "credentials"
    fake_json_method_output = {
        "foo": "bar",
    }
    mocked_json_method = MagicMock(
        return_value=fake_json_method_output
    )
    mocked_raise_for_status_method = MagicMock(
        return_value=None
    )
    mocked_sowprog_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )
    mocked_get = MagicMock(
        return_value=mocked_sowprog_response,
    )
    mocked_requests.get = mocked_get

    now = datetime.now()
    output = get_concert_infos_from_sowprog_api_with_date(
        date_to_search=now
    )

    mocked_http_basic_auth.assert_called_once_with(
        SOWPROG_EMAIL_CREDENTIAL,
        SOWPROG_PASSWORD,
    )

    mocked_get.assert_called_once_with(
        SOWPROG_URL,
        auth="credentials",
        headers={
            "Accept": "application/json"
        },
        params=(
            ('eventScheduleDate.date', "{}".format(now.strftime("%Y-%m-%d"))),
            ('past_events', 'True'),
        )
    )

    mocked_raise_for_status_method.assert_called_once()

    mocked_json_method.assert_called_once()

    assert output == fake_json_method_output


def test_unpack_and_check_sowprog_data_success():
    test_concert_data = {
        "eventDescriptionSplitByDate": [
            {
                "freeAdmission": "true",
                "event": {
                    "title": "Test_Title",
                    "eventStyle": {"label": "jazzapapa"},
                    "facebookFanPage": "fessedebouklolboomer",
                    "picture": "awesome_picture"
                }
            }
        ]
    }

    concert_name, concert_infos, error = unpack_and_check_sowprog_data(
        sowprog_raw_data=test_concert_data
    )

    assert concert_name == "Test_Title"

    expected_infos = {
        'title': "Test_Title",
        'facebook': "fessedebouklolboomer",
        'style': "jazzapapa",
        'free': "true",
        'picture': "awesome_picture",
    }
    assert concert_infos == expected_infos

    assert error is None


def test_unpack_and_check_sowprog_data_succes_no_concert_at_this_date():

    concert_name, concert_infos, error = unpack_and_check_sowprog_data(
        sowprog_raw_data={"eventDescriptionSplitByDate": []}
    )

    assert concert_name == "Sans concert"

    expected_infos = {
        'title': 'Sans concert',
        'facebook': '#',
        'style': '',
        'free': 'true',
                'picture': '#',
    }
    assert concert_infos == expected_infos

    assert error is None


def test_unpack_and_check_sowprog_data_error_bad_remote_data():
    concert_name, concert_infos, error = unpack_and_check_sowprog_data(
        sowprog_raw_data={}
    )

    assert concert_name == "Error with API"

    expected_infos = {
        'title': 'Sans concert',
        'facebook': '#',
        'style': '',
        'free': 'true',
        'picture': '#',
    }

    assert concert_infos == expected_infos

    assert isinstance(error, NotFound)
    assert error.description == "SowProgAPI failed to provide data"
    assert error.code == 404


def test_unpack_and_check_sowprog_data_error_too_many_concert_returned():
    test_concert_data = {
        "eventDescriptionSplitByDate": [
            {
                "freeAdmission": "true",
                "event": {
                    "title": "Test_Title_1",
                    "eventStyle": {"label": "jazzapapa"},
                    "facebookFanPage": "fessedebouklolboomer",
                    "picture": "awesome_picture"
                }
            },
            {
                "freeAdmission": "false",
                "event": {
                    "title": "Test_Title_2",
                    "eventStyle": {"label": "jazzamaman"},
                    "facebookFanPage": "bouhlenulilapafacebook",
                    "picture": "awful_picture"
                }
            }
        ]
    }

    concert_name, concert_infos, error = unpack_and_check_sowprog_data(
        sowprog_raw_data=test_concert_data
    )

    assert concert_name == "Multiples concerts"

    expected_infos = {
        'title': 'Sans concert',
        'facebook': '#',
        'style': '',
        'free': 'true',
        'picture': '#',
    }
    assert concert_infos == expected_infos

    assert isinstance(error, Conflict)
    assert error.description == "Too many data from SowProgAPI"
    assert error.code == 409

# --------------------- #
# Product Syncher tests #
# --------------------- #


@patch("project.synchers.ProductSyncher.get_remote_products")
@patch("project.synchers.ProductSyncher.batch_update_products_from_products")
@patch("project.synchers.ProductSyncher.batch_save_products")
def test_sync_products_success(
    mocked_batch_save_products: MagicMock,
    mocked_batch_update_products_from_products: MagicMock,
    mocked_get_remote_products: MagicMock,
):
    remote_product = Product()
    mocked_get_remote_products.return_value = [
        remote_product
    ]

    mocked_batch_update_products_from_products.return_value = [
        [],
        [
            remote_product
        ],
    ]

    created_products, updated_products = ProductSyncher.sync_products()

    mocked_get_remote_products.assert_called_once_with()

    mocked_batch_update_products_from_products.assert_called_once_with(
        first_party_products=[],
        third_party_products=[remote_product]
    )

    mocked_batch_save_products.assert_called_once_with(
        products_to_save=[remote_product]
    )

    assert created_products == [remote_product]
    assert updated_products == []


@patch("project.synchers.requests")
def test_get_remote_products_success(
    mocked_requests: NonCallableMagicMock,
):
    fake_initial_data = {
        "lastPage": 1,
    }
    fake_product_data = {
        "data": [
            {
                "id_product_global": "fake_id",
                "product_name": "product name",
                "product_price": 1.5,
                "id_product_type": 123456,
                "product_type": "a type",
                "id_category": "category_id",
                "category_name": "category_name",
                "category1": "category_1",
                "category2": "category_2",
                "tax_name": "20%",
                "place_send_name": None,
                "visible": 1,
                "removed": 0,
            }
        ]
    }
    mocked_json_method = MagicMock(
        side_effect=[
            fake_initial_data,
            fake_product_data,
        ]
    )
    mocked_raise_for_status_method = MagicMock(
        return_value=None
    )
    mocked_laddition_page_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )

    mocked_laddition_detail_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )
    mocked_get = MagicMock(
        side_effect=[
            mocked_laddition_page_response,
            mocked_laddition_detail_response,
        ],
    )

    mocked_requests.get = mocked_get

    third_party_products = ProductSyncher.get_remote_products()

    expected_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {LADDITION_AUTH_TOKEN}",
        "customerid": LADDITION_CUSTOMER_ID,
    }
    expected_get_calls = [
        call(
            ProductSyncher.menu_url,
            headers=expected_headers,
        ),
        call(
            f"{ProductSyncher.menu_url}?page=1",
            headers=expected_headers,
        )
    ]

    assert expected_get_calls == mocked_get.call_args_list

    expected_json_calls = [
        call(),
        call(),
    ]

    assert expected_json_calls == mocked_json_method.call_args_list

    expected_raise_for_status_calls = [
        call(),
        call()
    ]

    assert expected_raise_for_status_calls == mocked_raise_for_status_method.call_args_list

    assert len(third_party_products) == 1

    [third_party_product] = third_party_products

    assert third_party_product.uniq_id_product == "fake_id"
    assert third_party_product.product_name == "product name"
    assert third_party_product.product_price == 1.5
    assert third_party_product.id_product_type == 123456
    assert third_party_product.id_category == "category_id"
    assert third_party_product.category_name == "category_name"
    assert third_party_product.category1 == "category_1"
    assert third_party_product.category2 == "category_2"
    assert third_party_product.tax_name == "20%"
    assert third_party_product.place_send_name is None
    assert third_party_product.visible
    assert not third_party_product.removed


@patch("project.synchers.requests")
def test_get_remote_products_success_error_in_detail_request(
    mocked_requests: NonCallableMagicMock,
    caplog,
):
    fake_initial_data = {
        "lastPage": 1,
    }
    fake_product_data = {
        "data": [
            {
                "id_product_global": "fake_id",
                "product_name": "product name",
                "product_price": 1.5,
                "id_product_type": 123456,
                "product_type": "a type",
                "id_category": "category_id",
                "category_name": "category_name",
                "category1": "category_1",
                "category2": "category_2",
                "tax_name": "20%",
                "place_send_name": None,
                "visible": 1,
                "removed": 0,
            }
        ]
    }
    mocked_json_method = MagicMock(
        side_effect=[
            fake_initial_data,
            fake_product_data,
        ]
    )
    mocked_raise_for_status_method = MagicMock(
        side_effect=[
            None,
            HTTPError()
        ]
    )
    mocked_laddition_page_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )

    mocked_laddition_detail_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )
    mocked_get = MagicMock(
        side_effect=[
            mocked_laddition_page_response,
            mocked_laddition_detail_response,
        ],
    )

    mocked_requests.get = mocked_get

    third_party_products = ProductSyncher.get_remote_products()

    expected_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {LADDITION_AUTH_TOKEN}",
        "customerid": LADDITION_CUSTOMER_ID,
    }
    expected_get_calls = [
        call(
            ProductSyncher.menu_url,
            headers=expected_headers,
        ),
        call(
            f"{ProductSyncher.menu_url}?page=1",
            headers=expected_headers,
        )
    ]

    assert expected_get_calls == mocked_get.call_args_list

    expected_json_calls = [
        call(),
    ]

    assert expected_json_calls == mocked_json_method.call_args_list

    expected_raise_for_status_calls = [
        call(),
        call()
    ]

    assert expected_raise_for_status_calls == mocked_raise_for_status_method.call_args_list

    http_detail_log_record, _timer_log_record = caplog.records

    assert http_detail_log_record.levelname == "ERROR"
    assert http_detail_log_record.message == "Failed to load page 1 due to network error"

    assert len(third_party_products) == 0


@patch("project.synchers.requests")
def test_get_remote_products_error_in_initial_request(
    mocked_requests: NonCallableMagicMock,
):
    mocked_json_method = MagicMock(
        side_effect=[
            AssertionError("Json method of response should not have been called")]
    )
    mocked_raise_for_status_method = MagicMock(
        side_effect=[
            HTTPError()
        ]
    )
    mocked_laddition_page_response = NonCallableMagicMock(
        spec=[],
        json=mocked_json_method,
        raise_for_status=mocked_raise_for_status_method,
    )

    mocked_get = MagicMock(
        side_effect=[
            mocked_laddition_page_response,
            AssertionError("Detail page should not have been called"),
        ],
    )

    mocked_requests.get = mocked_get

    with pytest.raises(HTTPError):
        ProductSyncher.get_remote_products()

    expected_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {LADDITION_AUTH_TOKEN}",
        "customerid": LADDITION_CUSTOMER_ID,
    }
    expected_get_calls = [
        call(
            ProductSyncher.menu_url,
            headers=expected_headers,
        ),
    ]

    assert expected_get_calls == mocked_get.call_args_list

    mocked_json_method.assert_not_called()

    expected_raise_for_status_calls = [
        call(),
    ]

    assert expected_raise_for_status_calls == mocked_raise_for_status_method.call_args_list


def test_batch_update_products_from_products_success():
    existing_product_1 = Product(
        uniq_id_product='existing_id_1',
        product_name='product_name_1',
        product_price=1.5,
        id_product_type=1234567,
        product_type='product_type',
        id_category='id_category',
        category_name='category_name',
        category1='category1',
        category2='category2',
        tax_name='20%',
        place_send_name=None,
        visible=True,
        removed=False,
    )
    existing_product_2 = Product(
        uniq_id_product='existing_id_2',
        product_name='product_name_2',
        product_price=1.5,
        id_product_type=1234567,
        product_type='product_type_2',
        id_category='id_category_2',
        category_name='category_name_2',
        category1='category1_2',
        category2='category2_2',
        tax_name='20%',
        place_send_name=None,
        visible=True,
        removed=False,
    )

    DB_ORM.session.bulk_save_objects([existing_product_1, existing_product_2])
    DB_ORM.session.commit()

    remote_product_1 = Product(  # Has changed
        uniq_id_product='existing_id_1',
        product_name='product_name_1',
        product_price=4,  # Changed
        id_product_type=1234567,
        product_type='product_type',
        id_category='id_category',
        category_name='category_name',
        category1='category1',
        category2='category2',
        tax_name='20%',
        place_send_name=None,
        visible=False,  # Changed
        removed=False,
    )
    remote_product_2 = Product(  # Has not changed
        uniq_id_product='existing_id_2',
        product_name='product_name_2',
        product_price=1.5,
        id_product_type=1234567,
        product_type='product_type_2',
        id_category='id_category_2',
        category_name='category_name_2',
        category1='category1_2',
        category2='category2_2',
        tax_name='20%',
        place_send_name=None,
        visible=True,
        removed=False,
    )
    remote_product_3 = Product(  # Is new
        uniq_id_product='existing_id_3',
        product_name='product_name_3',
        product_price=1.5,
        id_product_type=1234567,
        product_type='product_type_3',
        id_category='id_category_3',
        category_name='category_name_3',
        category1='category1_3',
        category2='category2_3',
        tax_name='20%',
        place_send_name=None,
        visible=True,
        removed=False,
    )

    third_party_products = [
        remote_product_1,
        remote_product_2,
        remote_product_3,
    ]

    first_party_products = Product.query.filter(
        Product.uniq_id_product.in_(
            [
                product.uniq_id_product
                for product in third_party_products
            ]
        )
    ).all()

    updated_products, products_to_create = ProductSyncher.batch_update_products_from_products(
        first_party_products=first_party_products,
        third_party_products=third_party_products,
    )

    product_1_from_db, product_2_from_db = first_party_products

    assert updated_products == [product_1_from_db]
    # Product 2 is untouched
    assert products_to_create == [remote_product_3]

    assert product_1_from_db.product_price == 4
    assert not product_1_from_db.visible


def test_batch_update_products_from_products_success_no_products_to_update():
    remote_product_1 = Product(
        uniq_id_product='fooBar',
        product_name='product_name',
        product_price=4,
        id_product_type=1234567,
        product_type='product_type',
        id_category='id_category',
        category_name='category_name',
        category1='category1',
        category2='category2',
        tax_name='20%',
        place_send_name=None,
        visible=False,
        removed=False,
    )
    remote_product_2 = Product(
        uniq_id_product='BarFoo',
        product_name='product_name_2',
        product_price=1.5,
        id_product_type=1234567,
        product_type='product_type_2',
        id_category='id_category_2',
        category_name='category_name_2',
        category1='category1_2',
        category2='category2_2',
        tax_name='20%',
        place_send_name=None,
        visible=True,
        removed=False,
    )

    third_party_products = [
        remote_product_1,
        remote_product_2,
    ]

    first_party_products = Product.query.filter(
        Product.uniq_id_product.in_(
            [
                product.uniq_id_product
                for product in third_party_products
            ]
        )
    ).all()

    updated_products, products_to_create = ProductSyncher.batch_update_products_from_products(
        first_party_products=first_party_products,
        third_party_products=third_party_products,
    )

    assert updated_products == []

    assert products_to_create == [remote_product_1, remote_product_2]
