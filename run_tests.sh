#!/usr/bin/env bash

pipenv run coverage run -m pytest -v && pipenv run coverage html
pipenv run mypy .


