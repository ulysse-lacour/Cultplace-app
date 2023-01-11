from unittest.mock import patch

import pytest
from flask import Flask, url_for
from flask.testing import FlaskClient
from project.auth import (
    EXISTING_USER_MESSAGE,
    NOT_IMPLEMENTED_ERROR_MESSAGE,
    RETRY_MESSAGE
)
from project.models.auth import User

from .conftest import DB_ORM, TEST_USER_CREDENTIALS, AuthActions


def test_get_login(client: FlaskClient, app: Flask):
    with app.app_context(), app.test_request_context():

        response = client.get(url_for("auth.login"), follow_redirects=True)

        assert response.status_code == 200


def test_post_login_success(auth: AuthActions, app: Flask):
    with app.app_context(), app.test_request_context():
        response = auth.login(
            email=TEST_USER_CREDENTIALS['email'],
            password=TEST_USER_CREDENTIALS['password'],
        )
        assert response.status_code == 200
        assert response.request.path == url_for("main.profile")
        assert RETRY_MESSAGE not in response.get_data(as_text=True)


def test_post_login_error_no_user(app: Flask, auth: AuthActions):
    with app.app_context(), app.test_request_context():
        response = auth.login(
            email="fake@email.fake",
            password=TEST_USER_CREDENTIALS['password'],
        )

        assert response.status_code == 200
        assert response.request.path == url_for("auth.login")
        assert RETRY_MESSAGE in response.get_data(as_text=True)


def test_post_login_error_wrong_password(app: Flask, auth: AuthActions):
    with app.app_context(), app.test_request_context():
        response = auth.login(
            email=TEST_USER_CREDENTIALS['email'],
            password="fake_password",
        )

        assert response.status_code == 200
        assert response.request.path == url_for("auth.login")
        assert RETRY_MESSAGE in response.get_data(as_text=True)


@patch("project.auth.FLASK_ENV", "production")
def test_get_signup_success_production(
    app: Flask,
    client: FlaskClient,
):
    with app.app_context(), app.test_request_context():
        response = client.get(
            url_for("auth.signup"),
        )

        assert response.status_code == 403
        assert NOT_IMPLEMENTED_ERROR_MESSAGE in response.get_data(as_text=True)


@patch("project.auth.FLASK_ENV", "development")
def test_get_signup_success_development(
    app: Flask,
    client: FlaskClient,
):
    with app.app_context(), app.test_request_context():
        response = client.get(
            url_for("auth.signup"),
        )

        assert response.status_code == 200
        assert response.request.path == url_for("auth.signup")


@patch("project.auth.FLASK_ENV", "production")
def test_post_signup_success_production(
    app: Flask,
    client: FlaskClient,
):
    with app.app_context(), app.test_request_context():
        response = client.post(
            url_for("auth.signup"),
            data={
                "email": "new_email@to_register.com",
                "name": "New User",
                "password": "new_password",
                "company": "New Company",
            }
        )

        assert response.status_code == 403
        assert NOT_IMPLEMENTED_ERROR_MESSAGE in response.get_data(as_text=True)


@patch("project.auth.FLASK_ENV", "development")
def test_post_signup_success_developement(
    app: Flask,
    client: FlaskClient,
):
    with app.app_context(), app.test_request_context():
        response = client.post(
            url_for("auth.signup"),
            data={
                "email": "new_email@to_register.com",
                "name": "New User",
                "password": "new_password",
                "company": "New Company",
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert response.request.path == url_for("auth.login")

        created_user = User.query.filter_by(email="new_email@to_register.com").first()

        assert created_user is not None


@patch("project.auth.FLASK_ENV", "development")
def test_post_signup_success_existing_user(
    app: Flask,
    client: FlaskClient,
):
    with app.app_context(), app.test_request_context():
        # Create a user
        client.post(
            url_for("auth.signup"),
            data={
                "email": "new_email@to_register.com",
                "name": "New User",
                "password": "new_password",
                "company": "New Company",
            }
        )

        # Try to create a user with the same email
        response = client.post(
            url_for("auth.signup"),
            data={
                "email": "new_email@to_register.com",
                "name": "A different user",
                "password": "with the same mail",
                "company": "clearly different company",
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert response.request.path == url_for("auth.signup")
        assert EXISTING_USER_MESSAGE in response.get_data(as_text=True)


def test_get_logout_success(auth: AuthActions, app: Flask):
    with app.app_context(), app.test_request_context():
        auth.login(
            email=TEST_USER_CREDENTIALS['email'],
            password=TEST_USER_CREDENTIALS['password'],
        )
        response = auth.logout()
        assert response.status_code == 200
        assert response.request.path == url_for("main.index")


def test_get_logout_success_not_logged(auth: AuthActions, app: Flask):
    with app.app_context(), app.test_request_context():
        response = auth.logout()
        assert response.status_code == 200
        assert response.request.path == url_for("auth.login")
