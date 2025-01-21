#!/bin/bash

# extract databasepath from config.toml
DB_PATH=$(python -c "
import tomllib
with open('config.toml', 'rb') as f:
    config = tomllib.load(f)
print(config['CompetitionServer']['database_path'])
")

if [ -e "${DB_PATH}" ]; then
    echo "Database ${DB_PATH} already exists."
    exit 1
fi


# create database
python -m comprl.scripts.create_database ./config.toml

python ../comprl-web-reflex/create_database_tables.py "${DB_PATH}"

# add bot users
comprl-users add "${DB_PATH}" bot-weak --role bot --password $(uuidgen)
comprl-users add "${DB_PATH}" bot-strong --role bot --password $(uuidgen)
