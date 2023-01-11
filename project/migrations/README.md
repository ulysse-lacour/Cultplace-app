- [Migrations](#migrations)
    - [Update your DB to latest migration](#update-your-db-to-latest-migration)
    - [Register the changes you made to models (and applying them)](#register-the-changes-you-made-to-models-and-applying-them)

# Migrations

> Migrations are the only way to keep a track of database modifications across the time. They insure that the data migrate as well as the DB schema.

Please read carefully [flask-migrate documention](https://flask-migrate.readthedocs.io/en/latest/#example) (flask-migrate is a flask wrapper for [alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
SQLAlchemy's migration system)

Migrations can be found in `project/migrations/versions` ([link](versions/))

### Update your DB to latest migration

```
pipenv run Flask db upgrade
```

> You must have run this code at least once to generate new migrations

If you need to point a specific migration, do as follows

```
pipenv run Flask db upgrade a544b70486c2
```

> `a544b70486c2` is the identifier of the targetted migration

### Register the changes you made to models (and applying them)

```
$ pipenv run Flask db migrate -m "_24_name_of_migration"
$ pipenv run Flask db upgrade
```

> Always start the name of your migration by `_{index_of_migration}_` in order to keep track of this order.



