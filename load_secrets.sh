#!/usr/bin/env bash

FILE=.env
if test -f "$FILE"; then
    rm -f .env
    unzip -o env_secrets.zip
else
    unzip -o env_secrets.zip
fi
