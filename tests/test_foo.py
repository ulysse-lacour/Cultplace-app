import pdb
from unittest.mock import patch, MagicMock
from decimal import Decimal
from typing import Optional
import json
import pytest
import requests


class APIError(Exception):
    pass


class BankSyncher(object):
    api_url = "https://my_foo_bank.com/api/v2/"
    income_endpoint = "income/"
    outcome_endpoint = "outcome/"

    @classmethod
    def register_income(cls, income: Decimal) -> None:
        """
        Register income to the bank
        """
        response = requests.post(
            "".join(
                [
                    cls.api_url,
                    cls.income_endpoint
                ]
            ),
            json={"income": float(income)}
        )

        if response.status_code != 200:
            raise APIError(f"Could not register income: {response.text}")

    @classmethod
    def register_outcome(cls, outcome: Decimal) -> Optional[Decimal]:
        """
        Register outcome to the bank
        """
        response = requests.post(
            "".join(
                [
                    cls.api_url,
                    cls.outcome_endpoint
                ]
            ),
            json={"outcome": float(outcome)}
        )

        if response.status_code != 200:
            raise APIError(f"Could not register outcome: {response.text}")

        return cls.read_balance()

    @classmethod
    def read_balance(cls) -> Optional[Decimal]:
        """
        Read the balance from the bank
        """
        response = requests.get(
            "".join(
                [
                    cls.api_url,
                    "balance"
                ]
            )
        )

        if response.status_code != 200:
            raise APIError(f"Could not read balance: {response.text}")

        response_data = json.loads(response.json())
        return Decimal(response_data["balance"])


class Concert(object):
    def __init__(
        self,
        band: str,
        location: str,
        entry_price: Decimal,
    ) -> None:
        self.band = band
        self.location = location
        self.entry_price = entry_price
        self.total_audience = 0

    def __repr__(self) -> str:
        return f"<{self.band} in {self.location}>"

    def sell_ticket(
        self,
        tip: Decimal = Decimal(0)
    ) -> bool:

        financial_balance = BankSyncher.register_income(income=self.entry_price + tip)

        if financial_balance is None:
            return False
        else:
            self.total_audience += 1
            return True

    def refund_ticket(self) -> bool:

        if self.band == "La Rue Kétanou":
            raise ValueError("La flemme gros t'as pas une roulée")

        self._assert_can_refund()

        financial_balance = BankSyncher.register_outcome(outcome=self.entry_price)

        if financial_balance is None:
            return False
        else:
            self.total_audience -= 1  # Let's fix this, old version didn't have the feature
            return True

    def _assert_can_refund(self):
        deducted_budget = self.get_budget_available() - self.entry_price
        if deducted_budget < 0:
            raise ValueError(f"Cannot refund entry, deducted budget would be {str(deducted_budget)}")

    def get_budget_available(self):
        return BankSyncher.read_balance()


def test_concert___repr__():
    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )
    concert_repr = concert.__repr__()

    assert concert_repr == "<Test Band in Test Location>"


@patch(
    "tests.test_foo.BankSyncher.register_income",  # The name to patch
    return_value=Decimal("100.00"),
    # The replacement value returned when the name is called during execution of the patched function.
)
def test_concert_sell_entry_success(
    mock_register_income: MagicMock,
):
    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    has_succeded = concert.sell_ticket(tip=Decimal("5"))

    mock_register_income.assert_called_once_with(
        income=Decimal("15")
    )
    assert has_succeded is True


@patch(
    "tests.test_foo.BankSyncher.register_income",  # The name to patch
    return_value=None,
    # The replacement value returned when the name is called during execution of the patched function.
)
def test_concert_sell_entry_success_register_income_returned_none(
    mock_register_income: MagicMock,
):
    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    has_succeded = concert.sell_ticket(tip=Decimal("5"))

    mock_register_income.assert_called_once_with(
        income=Decimal("15")
    )
    assert has_succeded is False


@patch("tests.test_foo.BankSyncher.register_outcome")
@patch("tests.test_foo.Concert._assert_can_refund")
def test_concert_refund_entry_success_budget(
    mocked_assert_can_refund: MagicMock,
    mocked_register_outcome: MagicMock,
):

    mocked_register_outcome.return_value = Decimal("100")

    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    has_succeded = concert.refund_ticket()

    mocked_assert_can_refund.assert_called_once()
    mocked_register_outcome.assert_called_once_with(outcome=Decimal("10.00"))
    assert has_succeded is True


@patch("tests.test_foo.BankSyncher.register_outcome")
@patch("tests.test_foo.Concert._assert_can_refund")
def test_concert_refund_entry_success_budget_register_outcome_returned_none(
    mocked_assert_can_refund: MagicMock,
    mocked_register_outcome: MagicMock,
):

    mocked_register_outcome.return_value = None

    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    has_succeded = concert.refund_ticket()

    mocked_assert_can_refund.assert_called_once()
    mocked_register_outcome.assert_called_once_with(outcome=Decimal("10.00"))
    assert has_succeded is False


@patch("tests.test_foo.Concert.get_budget_available")
def test_concert_refund_entry_error_budget_incapacity(
    mocked_get_budget_available: MagicMock,
):
    mocked_get_budget_available.return_value = Decimal("0")

    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )
    with pytest.raises(ValueError) as excinfo:
        budget_available = concert.refund_ticket()
    assert "Cannot refund entry, deducted budget would be -10.00" in str(excinfo.value)


def test_concert_refund_entry_error_stingy_band():
    concert = Concert(
        band="La Rue Kétanou",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    with pytest.raises(ValueError) as excinfo:
        concert.refund_ticket()

    assert "La flemme gros t'as pas une roulée" in str(excinfo.value)


@patch("tests.test_foo.BankSyncher.read_balance")
@patch("tests.test_foo.BankSyncher.register_income")
@patch("tests.test_foo.BankSyncher.register_outcome")
def test_concert_flow_sell_and_refund_entry_success(
    mocked_register_outcome: MagicMock,
    mocked_register_income: MagicMock,
    mocked_read_balance: MagicMock,
):
    mocked_read_balance.return_value = Decimal("100")
    mocked_register_income.return_value = Decimal("100")
    mocked_register_outcome.return_value = Decimal("100")

    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    sale_success = concert.sell_ticket()

    mocked_register_income.assert_called_once_with(income=Decimal("10.00"))
    assert sale_success is True

    refund_success = concert.refund_ticket()

    mocked_read_balance.assert_called_once()
    mocked_register_outcome.assert_called_once_with(outcome=Decimal("10.00"))
    assert refund_success is True


@patch("tests.test_foo.BankSyncher.read_balance")
@patch("tests.test_foo.BankSyncher.register_income")
@patch("tests.test_foo.BankSyncher.register_outcome")
def test_concert_flow_sell_and_refund_entry_error_band_has_changed(
    mocked_register_outcome: MagicMock,
    mocked_register_income: MagicMock,
    mocked_read_balance: MagicMock,
):
    mocked_read_balance.return_value = Decimal("100")
    mocked_register_income.return_value = Decimal("100")
    mocked_register_outcome.return_value = Decimal("100")

    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    sale_success = concert.sell_ticket()
    mocked_register_income.assert_called_once_with(income=Decimal("10.00"))
    assert sale_success is True

    concert.band = "La Rue Kétanou"
    with pytest.raises(ValueError) as excinfo:
        concert.refund_ticket()

    mocked_read_balance.assert_not_called()
    mocked_register_outcome.assert_not_called()
    assert "La flemme gros t'as pas une roulée" in str(excinfo.value)


@patch("tests.test_foo.requests")
def test_BankSyncher_register_income_success(
    mocked_request: MagicMock,
):
    income = Decimal("100.00")
    fake_post = MagicMock(
        return_value=MagicMock(status_code=200),
    )

    mocked_request.post = fake_post

    register_income_output = BankSyncher.register_income(income=income)

    fake_post.assert_called_once_with(
        "https://my_foo_bank.com/api/v2/income/",
        json={"income": float(income)}
    )

    assert register_income_output is None


@patch("tests.test_foo.requests")
def test_BankSyncher_register_income_error_forbidden(
    mocked_request: MagicMock,
):
    income = Decimal("666")
    fake_post = MagicMock(
        return_value=MagicMock(status_code=403, text=income),
    )

    mocked_request.post = fake_post

    with pytest.raises(APIError) as excinfo:
        BankSyncher.register_income(income=income)
        fake_post.assert_called_once_with(
            "https://my_foo_bank.com/api/v2/income/",
            json={"income": float(income)}
        )
    assert "Could not register income: 666" in str(excinfo.value)


@patch("tests.test_foo.requests")
@patch("tests.test_foo.BankSyncher.read_balance")
def test_BankSyncher_register_outcome_success(
    mocked_read_balance: MagicMock,
    mocked_request: MagicMock,
):

    mocked_read_balance.return_value = Decimal("6.66")
    outcome = Decimal("100.00")
    fake_post = MagicMock(
        return_value=MagicMock(status_code=200),
    )

    mocked_request.post = fake_post

    BankSyncher.register_outcome(outcome=outcome)

    fake_post.assert_called_once_with(
        "https://my_foo_bank.com/api/v2/outcome/",
        json={"outcome": float(outcome)}
    )


@patch("tests.test_foo.requests")
@patch("tests.test_foo.BankSyncher.read_balance")
def test_BankSyncher_register_outcome_error_forbidden(
    mocked_read_balance: MagicMock,
    mocked_request: MagicMock,
):

    mocked_read_balance.return_value = Decimal("6.66")
    outcome = Decimal("666")
    fake_post = MagicMock(
        return_value=MagicMock(status_code=403, text=outcome)
    )

    mocked_request.post = fake_post

    with pytest.raises(APIError) as excinfo:
        BankSyncher.register_outcome(outcome=outcome)

    fake_post.assert_called_once_with(
        "https://my_foo_bank.com/api/v2/outcome/",
        json={"outcome": float(outcome)}
    )
    assert "Could not register outcome: 666" in str(excinfo.value)


@patch("tests.test_foo.requests")
def test_BankSyncher_read_balance_success(
    mocked_request: MagicMock,
):
    remote_balance = "6.66"
    balance_response = {"balance": remote_balance}
    fake_json_method = MagicMock(
        return_value=json.dumps(balance_response)
    )
    fake_get = MagicMock(
        return_value=MagicMock(status_code=200, json=fake_json_method)
    )
    mocked_request.get = fake_get

    read_balance_output = BankSyncher.read_balance()

    fake_get.assert_called_once_with(
        "https://my_foo_bank.com/api/v2/balance"
    )

    assert read_balance_output == Decimal(remote_balance)


@patch("tests.test_foo.requests")
def test_BankSyncher_read_balance_error_forbidden(
    mocked_request: MagicMock,
):
    remote_balance = "666"
    fake_get = MagicMock(
        return_value=MagicMock(status_code=403, text=remote_balance)
    )
    mocked_request.get = fake_get

    with pytest.raises(APIError) as excinfo:
        BankSyncher.read_balance()
        fake_get.assert_called_once_with(
            "https://my_foo_bank.com/api/v2/balance"
        )
    assert "Could not read balance: 666" in str(excinfo.value)
