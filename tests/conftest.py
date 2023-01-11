import os
import pytest

from flask import Flask
from flask.testing import FlaskClient
from project import app as app_factory
from project.models.auth import User
from project.settings import DB_ORM
from werkzeug.security import generate_password_hash
from werkzeug.test import TestResponse

TEST_USER_CREDENTIALS = {
    "email": "bar@foo.com",
    "password": "password",
    "name": "Foo Bar User",
    "company": "Foo Bar Company",
    "super_user": False,
}

TEST_ADMIN_USER_CREDENTIALS = {
    "email": "admin@admin.com",
    "password": "admin_password",
    "name": "Admin User",
    "company": "MaPetiteEntreprise",
    "super_user": True,
}


@pytest.fixture(scope="session")  # The scope let you define how "reusable" a fixture is, session means "test session".
def app():
    # Start by creating an app like we always do
    app = app_factory.initialize_app(testing=True)

    # Set the APP in testing mode
    app.config.update(
        {
            'TESTING': True,
        }
    )

    if os.getenv("CI_ENV") is not None:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI_DEV")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://test:test@localhost/test"

    DB_ORM.init_app(app)
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
        # Setup an admin user in the DB
        DB_ORM.session.add(
            User(
                email=TEST_ADMIN_USER_CREDENTIALS['email'],
                password=generate_password_hash(
                    TEST_ADMIN_USER_CREDENTIALS["password"],
                    method='sha256'
                ),
                name=TEST_ADMIN_USER_CREDENTIALS['name'],
                company=TEST_ADMIN_USER_CREDENTIALS['company'],
                super_user=TEST_ADMIN_USER_CREDENTIALS['super_user'],
            )
        )

        DB_ORM.session.commit()

        # Return the app
        yield app

        # Cleaning test db
        DB_ORM.session.remove()
        DB_ORM.drop_all()

    # clean up / reset resources here


@pytest.fixture(scope="session")
def client(app: Flask):
    return app.test_client()


class AuthActions(object):
    def __init__(self, client: FlaskClient) -> None:
        # Is born with a client
        self._client = client

    def login(
        self,
        email=TEST_USER_CREDENTIALS['name'],
        password=TEST_USER_CREDENTIALS['password'],
    ) -> TestResponse:
        return self._client.post(
            '/login',
            data={
                'email': email,
                'password': password,
            },
            follow_redirects=True
        )

    def logout(self) -> TestResponse:
        return self._client.get('/logout', follow_redirects=True)


@pytest.fixture(scope="function")
def auth(client: FlaskClient) -> AuthActions:
    return AuthActions(client)
