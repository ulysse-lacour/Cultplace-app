#!/usr/bin/env bash

FILE=.env
if test -f "$FILE"; then
    zip -er env_secrets.zip .env
else
    echo "No .env file found"
fi
