CompRL Hockey Game
==================

Implementation of the Hockey game for the comprl server.

## Requirements

Before running, install the requirements:
```
pip install -r requirements.txt
```

And initialise the database:
```
python3 -m comprl.scripts.create_database ./config.toml
```


## Run the server

Call from this directory (otherwise relative paths in the config will not be resolved
correctly):
```
python3 -m comprl.server --config ./config.toml
```


## Evaluation

### Statistics

There is a Jupyter notebook `Evaluation.ipynb` to run some statistical evaluation of the
games.  Simply set the path to the database at the top of the notebook and run it.


### Generate Videos

The script `render_game.py` can be used to view recorded games and to save them as
videos.  Run with `--help` to see all options.

There is also a script `select_top_player_games.py` to randomly select some games of the
best users.  Together they may be used to generate videos of some top games:
```sh
python select_top_player_games.py path/to/database.db > games.txt
cat games.txt | parallel --csv python render_game.py path/to/game_actions/{3}.pkl --save-video {1}_vs_{2}.mp4
```
(you may need to install `parallel` first)
