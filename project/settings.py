import os

from flask_sqlalchemy import SQLAlchemy


APP_NAME = 'project.app'
DB_ORM = SQLAlchemy()
FLASK_ENV = os.getenv("FLASK_ENV")

if FLASK_ENV == "development":
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI_DEV",
    )
elif FLASK_ENV == "production":
    # To use prod urls, please edit /cultplace/.env with 'FLASK_ENV = PROD'
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI_PROD")
else:
    raise RuntimeError(
        "Unexpected environement variable 'FLASK_ENV', "
        "expected values : 'production' or 'development', "
        f"got {str(FLASK_ENV)}"
    )

SOWPROG_EMAIL_CREDENTIAL = os.getenv("SOWPROG_EMAIL_CREDENTIAL")
SOWPROG_PASSWORD = os.getenv("SOWPROG_PASSWORD")

LADDITION_AUTH_TOKEN = os.getenv("LADDITION_AUTHORIZATION_TOKEN")
LADDITION_CUSTOMER_ID = os.getenv("LADDITION_CUSTOMER_ID")
