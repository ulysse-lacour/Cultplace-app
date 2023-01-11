- [Testing for Cultplace](#testing-for-cultplace)
  - [Launch test & coverage for the app](#launch-test--coverage-for-the-app)
  - [Where to setup your tests](#where-to-setup-your-tests)
- [Testing in general](#testing-in-general)
  - [Test basic tutorial](#test-basic-tutorial)
    - [General purpose](#general-purpose)
    - [Context](#context)
    - [What to test](#what-to-test)
    - [Tests breakdown](#tests-breakdown)
      - [Succes tests](#succes-tests)
      - [Error tests](#error-tests)
      - [Integration tests](#integration-tests)
  - [Advanced™️ testing with patches and fixtures](#advanced️-testing-with-patches-and-fixtures)
    - [Patches & Mocks](#patches--mocks)
    - [Pytest's fixtures](#pytests-fixtures)

# Testing for Cultplace

> For the purpose of testing Cultplace, we are using [pytest](https://docs.pytest.org/en/7.1.x/)
> It should be already installed and accessible through `pipenv run`

## Launch test & coverage for the app

```
// Run all the tests + Generate coverage report
(cultplace) % ./run_tests.sh

// run 1 specific test
(cultplace) % pipenv run pytest -k "test_foo_success"
```

You can access the coverage review inside `./htmlcov/index.html` (not included in the repo, you'll have to run `run-tests.sh` once first)

## Where to setup your tests

All tests should go in the `tests` module, and should be named `test_name_of_test.py` in order for the test engine to find it when running `run_tests.sh`

# Testing in general

> #️⃣ For the code of this section, you can acces [test_foo.py](./test_foo.py)

## Test basic tutorial

### General purpose

A test is a function whose only purpose is to assert that, with a given input, it behave as it should, and output as expected.

### Context

Let's take a Concert interface. It represents a concert event, with a band playing, tickets being sold, audience being quantified, etc.

```python
class Concert(object):
    def __init__(
        self,
        band: str,
        location: str,
        entry_price: Decimal,
        entrance_number: str,
        base_budget: Decimal
    ) -> None:
        self.band = band
        self.entry_price = entry_price
        self.entrance_number = entrance_number
        self.income = 0
        self.total_audience = 0
        self.base_budget = base_budget
```

You can use this interface to sell a ticket, and increase the income of your concert event, with the method `sell_ticket`

```python
def sell_ticket(self, tip: Optional[Decimal] = 0) -> bool:
    self.income += self.entry_price + tip
    self.total_audience += 1

    return True
```

If someone were to cancel their concert plan, then the event organzier would need to refund the ticket. Hopefully, there is a method for that.

```python
def refund_ticket(self) -> bool:

    self._assert_can_refund()  # First make sure the organizer have the money

    if self.band == "La Rue Kétanou":  # Or that he is not stingy (this assertion could semantically happen in _assert_can_refund)
        raise ValueError("La flemme gros t'as pas une roulée")

    self.income -= self.entry_price

    return self.budget_available

def _assert_can_refund(self):
    deducted_budget = (self.income + self.base_budget) - self.entry_price
    if deducted_budget < 0:
        raise ValueError(f"Cannot refund entry, deducted budget would be {str(deducted_budget)}")

```

> Notice `self.budget_available`, which is a property of the class. Properties are computed attributes.

```python
@property
def budget_available(self):
    return self.income + self.base_budget
```

Now, we want to be sure that this interface will always behave as expected....

### What to test

**Test every logical branch of your function/view/class**. If you are testing an abstraction, let's say a class or a flask view, test the high level interactions as well as the low level.

It we take our `Concert` interface, we have a lot to test.

- Our interface should be able to sell 1 ticket to a client, and have the amount added to its income
- It should be able of refunding a ticket
  - if it has the money
- It should raise an error if:
  - The band is a stingy one
  - It does not hold enough money (including `base_budget`, which is what the organizer had before the convert event)

This logical division, above, is the way this simple class can be tested. It shows how to unit-test.

### Tests breakdown

> #️⃣ If you want to access the commit of this branch, [follow this link](https://github.com/ElJovial/cultplace/blob/94bc40031aba35fd4fe4066b281f325d009887a3/tests/test_foo.py)

#### Succes tests

> 💡 Tests names are easy to come with : `test` + `entity name` (class, function, etc.) + `description of interaction with entity` (can be a method name) + `success` / `error` + `condition that lead to success / error`

```python
def test_my_entity_my_interaction_success_conditon_of_success():
    ...
```

In our case, let's be pragmatic, and start by testing success scenario

- Our interface should be able to sell 1 ticket to a client, and have the amount added to its income

  ```python
  def test_concert_sell_entry_success():

      # Setup your data (here our interface) as it suits your test case
      concert = Concert(
          name="Test Concert",
          band="Test Band",
          location="Test Location",
          entry_price=Decimal("10.00"),
          entrance_number="Test Entrance Number",
          base_budget=Decimal("0")
      )

      # Provoke the interaction (with the maximum edge cases you can find, don't hesitate to write another test for another case)
      concert.sell_ticket(tip=Decimal("5"))

      # Assert the state of your entity has been altered / that the output of the function is as expected
      assert concert.income == Decimal("15")
  ```

#### Error tests

Let's now contemplate the case where the organizer starts with a debt, and is counting on this concert even to fill his purse. He would then not be able to refund any entry tickets, because all the money he is earning is refunding is own debt.

To test an error, we first need to make sure that raising this error will not break our test engine when the program raise it. To do so, `pytest` holds a nice context feature, allowing to assert the error is indeed the one we expect and also providing us with data describing the error.

```python
import pytest  # We need access to the pytest package inside our test file now

def test_concert_refund_entry_error_budget_incapacity():
    concert = Concert(
        name="Test Concert",
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
        entrance_number="Test Entrance Number",
        base_budget=Decimal("-100.00")  # Notice the organizer starts in debt
    )

    # If the wrong error (or no error) is raised, the context manager will raise an AssertionErrors
    with pytest.raises(ValueError) as excinfo:
        # Provoking interaction that should raise an error inside the context manager
        budget_available = concert.refund_ticket()

    assert "Cannot refund entry, deducted budget would be -110.00" in str(excinfo.value)
```

`pytest.raises()` is the context manager that will be responsible of asserting we indeed raise a `ValueError` and not a `RuntimeError`.
Inside this context, and after it is destroyed, lives the `excinfo` variable.
Access `excinfo.value` to have the raw error.

> 💡 For more precision we could have asked for a comparison between value error instead of string repr

#### Integration tests

> 💡 A lot of tests cases are named "integration tests". This is a presentation of the general concept.

Integration tests test a complex behavior of your application.

Because we are a serious service provider, and we want to ensure that the end user is able to do all operations in order, let's add a layer of security.

We will also test a user flow where the user buy a ticket, we assert the event has registered the income. Suddenly, the band has changed, and the user wants to be refunded, sadly the new band are now the stingy _La rue Kétanou_, thus an error is raised (because of stinginess 😇 ).

```python
def test_concert_flow_sell_and_refund_entry_error_band_has_changed():
    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
        entrance_number="Test Entrance Number",
        base_budget=Decimal("100.00")
    )

    concert.sell_ticket()
    assert concert.budget_available == Decimal("110.00")

    concert.band = "La Rue Kétanou"
    with pytest.raises(ValueError) as excinfo:
        concert.refund_ticket()

    assert "La flemme gros t'as pas une roulée" in str(excinfo.value)
```

## Advanced™️ testing with patches and fixtures

> #️⃣ [Code for this section lies here](https://github.com/ElJovial/cultplace/blob/9899a39e0870517f3530d407b183cfc37c1f5157/tests/test_foo.py)

We saw earlier how to test specific behaviour of our interface with unit testing. Our tests are quite straightforward, because the interface is absolutely self-contained.

What if, in order to know how much money we have, we need to first make an api call to our banking service ? We would expose our test to a failure of the API, **which API we are absolutely not responsible for testing**.

We will need to **patch** our call to the API. Let's start by extracting money management logic from our Concert interface in a new API interface, `BankSyncher`.

```python
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

        return Decimal(response.json()["balance"])
```

We are now able to talk to the bank service, and the concert should use this new piece of tech :

```python
class Concert(object):
    def __init__(
        self,
        band: str,
        location: str,
        entry_price: Decimal,
    ) -> None:
        self.band = band
        self.entry_price = entry_price
        self.total_audience = 0

    def __repr__(self) -> str:
        return f"< {self.name} by {self.band}>"

    def sell_ticket(
        self,
        tip: Optional[Decimal] = Decimal(0)
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
```

Note that all our tests of `Concert ` are now failing, raising a `requests.exceptions.ConnectionError`. While our tests of Concert still catch that something is wrong with the action of selling a ticket, we are now testing the internal logic of another self-contained object the `BankSyncher` class.

We want our unit tests for `Concert` methods to just tests the logic they are implementing, other implemented logic will be tested in addition.

> Logic `Concert.sell_ticket` is implementing that we want to test:
>
> - Do the action of registering a money entry
> - Return a boolean stating the success of the modification

This is the only logic we need to test for our interface. An external API error, on which we have absolutely no control over, could happen and fail the test. Without patches/mocks, our unit tests are now [nondeterministic](https://en.wikipedia.org/wiki/Nondeterministic_algorithm). Which is bad.

### Patches & Mocks

> Patches are used to change a name in the namespace of the function execution. Each call to the patched name will return the set output.

```python
form unittest.mock import patch, MagicMock

@patch(
    "tests.test_foo.BankSyncher.register_income",  # The name to patch
    return_value=Decimal("100.00") # The replacement value returned when the name is called during execution of the patched function.
)
def test_concert_sell_entry_success(
    mock_register_income: MagicMock,  # Explanation below
):
    concert = Concert(
        band="Test Band",
        location="Test Location",
        entry_price=Decimal("10.00"),
    )

    has_succeded = concert.sell_ticket(tip=Decimal("5"))

    # assert concert.income == Decimal("15") -> the income part will be tested in the BankSyncher unit tests

    assert has_succeded is True
```

Notice the presence of this new argument in the function argument : `mock_register_income`. A `MagicMock` object will be available in your test, which hold precious datas, like the number of time it has been called during the test execution, whith wich arguments it has been called, etc.

Let's go back to our previous test, and see if it, as expected, called the banking API interface :

```python
form unittest.mock import patch, MagicMock

@patch(
    "tests.test_foo.BankSyncher.register_income",
    return_value=Decimal("100.00")
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
    # to see full interactions and attribute of a mock, put a pdb here and run `pp(dir(mock_register_income))`

    assert has_succeded is True
```

We are now able to test specifically the logic of the function :

- The mock assert we do register the money, with a correct income amount (the `entry_price` + `tip` value)
- We assert the function has outputed a state about its resolution

And this is more or less what we need to know about mocks at this stage !

### Pytest's fixtures

Patches and mocks are part of the [python standard librairy](https://docs.python.org/3/library/), meaning that
they can be applied with different testing libraries (including the python standard `unittest` providing them, obviously).
On the other hand, [fixtures](https://docs.pytest.org/en/7.1.x/explanation/fixtures.html) are part of pytest test framework, and are useful tools for testing a Flask application.

For the purpose of this tutorial, and because I'm also new to pytest (@priandey speaking), I'll just land a link to [the documentation of pytest on how to use fixture](https://docs.pytest.org/en/7.1.x/how-to/fixtures.html), and describe how we are going to use them to test our flask application.

> **TLDR; Fixture are functions that you can be passed as argument inside a test**

In order to test flask views, wich are triggered by accessing url in a browser, we will need a client to make GET/POST
requests to our application, and we will also need our application to be alive and able to process and respond to HTTP™️ requests.
Hopefully, Flask is providing such a client for testing it's own views, as part of the app. We also need a live application
to process the requests.

Those 2 basic elements are thus needed in every tests for our views, and we will define fixtures for them in `conftest.py`

> [Link to conftest.py](conftest.py)

The `conftest.py` file is where the global fixtures will be defined, let's dissect it.

First we will need an app, so let's create one in a fixture

```python
from project import app as app_factory
from project.models.auth import User
from project.settings import DB_ORM
from werkzeug.security import generate_password_hash

@pytest.fixture(scope="session")  # The scope let you define how "reusable" a fixture is, session means "test session".
def app():
    # Start by creating an app like we always do
    app = app_factory.initialize_app()

    # Set the APP in testing mode
    app.config.update(
        {
            'TESTING': True,
        }
    )

    # Enter app context to have access to DB operations
    with app.app_context():
        # Create all the tables in the DB
        DB_ORM.create_all()

        # Setup a user in the DB
        DB_ORM.session.add(
            User(
                email=TEST_USER_CREDENTIALS['email'],
                password=generate_password_hash(
                    TEST_USER_CREDENTIALS["password"],
                    method='sha256'
                ),
                name=TEST_USER_CREDENTIALS['name'],
                company=TEST_USER_CREDENTIALS['company'],
                super_user=TEST_USER_CREDENTIALS['super_user'],
            )
        )
        DB_ORM.session.commit()

        # Return the app
        yield app

        # Cleaning test db
        DB_ORM.session.remove()
        DB_ORM.drop_all()

    # clean up / reset resources here
```

Second we also need the test client of the app. The good news is that fixtures can request other fixtures to operate.
Let's create the way simpler `client` fixture and see how you can request a fixture.

```python
@pytest.fixture(scope="session")
def client(app: Flask):
    return app.test_client()
```

Now, every tests that needs the client can request it by adding it to its expected arguments. See how we are going to
test if our logging view is correctly sent to our client.

> [Link for test_auth](test_auth.py)

```python
def test_get_login(client: FlaskClient, app: Flask):
    with app.app_context(), app.test_request_context():

        response = client.get(url_for("auth.login"), follow_redirects=True)

        assert response.status_code == 200
```

`with app.app_context(), app.test_request_context()` is a context manager. Inside of it,
there is a lot of information holded by both the context of the app and the context of the request. For instance, the `url_for("auth.login")` needs to be called inside an app context (same goes for the database connection, so if you need to do a query to the database those context are handy).

> This context thing is not 100% understood by me (@priandey), but I recommend for the
> time being to do every tests inside this context manager.

This was the test for a `GET` request on our logging view, it's pretty straightforward and should never fail.
For the purpose of testing the `POST` request on the same view, we could do the same, except there is more different cases
to tests :

- Login success
- Login fails due to a wrong email
- Login fails due to a wrong password

In order to avoir duplication of shared code, we will encapsulate the action of sending a post request to our logging view
into another fixture :

```python
class AuthActions(object):
    def __init__(self, client: FlaskClient) -> None:
        # Is born with a client
        self._client = client

    def login(
        self,
        email: str = TEST_USER_CREDENTIALS['name'],
        password: str = TEST_USER_CREDENTIALS['password'],  # Default guarantee the default output will be successfull
    ) -> None:
        return self._client.post(
            '/login',
            data={
                'email': email,
                'password': password,
            },
            follow_redirects=True
        )

    def logout(self) -> None:
        return self._client.get('/logout', follow_redirects=True)


@pytest.fixture(scope="function")
def auth(client: FlaskClient) -> AuthActions:
    return AuthActions(client)
```

A brand new `AuthActions` object will provided to every test requesting the `auth` fixture.

Here is an example of it's use

```python
def test_post_login_success(
    app: Flask,
    auth: AuthActions,
):
    with app.app_context(), app.test_request_context():
        response = auth.login(
            email=TEST_USER_CREDENTIALS['email'],
            password=TEST_USER_CREDENTIALS['password'],
        )
        assert response.status_code == 200
        assert response.request.path == url_for("main.profile")
        assert RETRY_MESSAGE not in response.get_data(as_text=True)
```

Note that we do no longer need the `client` fixture, as the client operations are dealt with inside
our `auth` fixture.

In order to understand better what are the fields of the response, I strongly encourage you to put a `pdb` just after
a response got generated, and inspect the response attributes with a `pp(var(response))` (for the data it holds) +
`pp(dir(response))` (to also have a peak on its methods).
