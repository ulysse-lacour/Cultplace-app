# auth.py

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import Forbidden
from project.settings import DB_ORM, FLASK_ENV
import os

from project.models.auth import User

auth = Blueprint('auth', __name__)

RETRY_MESSAGE = 'Please check your login details and try again.'
EXISTING_USER_MESSAGE = 'A user with that email already exists.'
NOT_IMPLEMENTED_ERROR_MESSAGE = "Route not implemented in production"


@auth.route('/login', methods=['GET'])
def login():
    if FLASK_ENV == "production":
        admin_user = User.query.filter_by(email=os.getenv("SUPER_USER_EMAIL")).first()
        if admin_user is None:
            # create super user
            admin_user = User(
                email=os.getenv("SUPER_USER_EMAIL"),
                name="Nhut",
                password=generate_password_hash(
                    os.getenv("SUPER_USER_PASSWORD"),
                    method='sha256'
                ),
                company="La Petite Halle",
                super_user=True,
            )
            DB_ORM.session.add(admin_user)
            DB_ORM.session.commit()
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash(RETRY_MESSAGE)
        # if user doesn't exist or password is wrong, reload the page
        return redirect(url_for('auth.login'))
    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))


@auth.route('/signup')
def signup():
    if (
        FLASK_ENV == "development"
        or (current_user.is_authenticated and current_user.super_user is True)
    ):
        return render_template('signup.html')
    else:
        return Forbidden(description=NOT_IMPLEMENTED_ERROR_MESSAGE)


@auth.route('/signup', methods=['POST'])
def signup_post():
    if FLASK_ENV == "development" or (current_user.is_authenticated and current_user.super_user is True):
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        company = request.form.get('company')

        # if this returns a user, then the email already exists in database
        user = User.query.filter_by(email=email).first()

        if user is not None:  # if a user is found, we want to redirect back to signup page so user can try again
            flash(EXISTING_USER_MESSAGE)
            return redirect(url_for('auth.signup'))

        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(
                password,
                method='sha256'
            ),
            company=company,
        )

        # add the new user to the database
        DB_ORM.session.add(new_user)
        DB_ORM.session.commit()
        return redirect(url_for('auth.login'))
    else:
        return Forbidden(NOT_IMPLEMENTED_ERROR_MESSAGE)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
