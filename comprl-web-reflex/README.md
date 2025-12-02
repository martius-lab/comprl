CompRL Web Interface with Reflex
================================

comprl-web-reflex is a re-implementation of the original web interface that was
done with Node.js.  It uses [reflex](reflex.dev), a Python framework for
building web applications.  The benefit of using Python is that it directly use
components of the comprl package (e.g.  for database access), thus reducing the
need for redundant code.  Further, it is easier to maintain as everything is
done with one language (Python).


## Features

- User registration
- Users statistics (number of played games, etc.)
- Leaderboard


## Requirements

To install the requirements (best do this in a virtual environment):
```
pip install ../comprl
pip install -r requirements.txt
```

The web interface needs an additional database table to manage login sessions.
To add it to an existing comprl database, run the following command:
```
python3 ./create_database_tables.py path/to/comprl/database.db
```


## Run

The path to the comprl config file needs to be specified via an environment
variable:
```
# Path to the database
export COMPRL_CONFIG_PATH="/path/to/comprl/config.toml"

reflex run
```

## Run with Docker

See [docs](../docs/how_to_docker.rst).
