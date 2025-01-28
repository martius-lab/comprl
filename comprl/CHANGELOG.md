# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- BREAKING: Removed option to use separate databases for user and game tables.
- BREAKING: Removed option to configure database table names.
- BREAKING: Database is not automatically created anymore.  Use
  `comprl.scripts.create_database`.
- BREAKING: New config option `data_dir` to specify output directory for game actions.
  This is a required setting (no default value), hence a breaking change.
- BREAKING: The server main script (`python -m comprl.server`) does not provide
  individual arguments to overwrite parameters anymore but instead uses a single
  argument `--config-overwrites` which expects a list of parameters like this:
  ```
  --config-overwrites port=1234 data_dir=/foo/bar ...
  ```
- BREAKING: `Agent` is now an abstract class and cannot be instantiated anymore.
  Instead, derive a custom class from it, that implements the `get_step` method.
- BREAKING: Relative paths in the config file are now resolved relative to the
  config file location instead of to the working directory.
- Matchmaking now samples from all candidates with quality above the threshold instead
  of using the first in the list.
- Do not update player ratings for games with disconnect.
- Add option to limit number of games run in parallel.

## Removed
- The `Agent.event` decorator has been removed.  Instead of using it, create
  a custom class that is derived from `Agent`.

## Added
- Script `list_games` to list all games from the database on the terminal.
- Helper function `comprl.client.launch_client`, which should make it easier to launch
  a client in a unified way.


## [0.1.0]

This is the final version of the University team project.

---
[Unreleased]: https://github.com/martius-lab/teamproject-competition-server/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/martius-lab/teamproject-competition-server/releases/tag/v0.1.0
