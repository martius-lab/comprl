# IDs

This Project has 3 types of IDs:
#### User-ID (int)

* Primary Key for the User database
* is linked to the matchmaking parameters and elo

#### Player-ID (UUID)

* Is used to handel and identify clients internally
* Only used during runtime
* There can be different players with the same User-ID

#### Game-ID (UUID)

* Is used to identify the game during runtime
* Is used as a primary key in the game database
* files name of the game files with all actions 


# Password/Token

#### Username and Password

* Used for login to the website
* can be freely chosen
* username is used for leaderboard

#### Token

* get from the website
* unique for every user (automatically generated)
* used for authentication when connecting an agent to the server

# AMP Protocol - `shared/commands`
![grafik](https://github.com/martius-lab/teamproject-competition-server/assets/116295458/ad04df99-6228-4033-98fa-af8e1a05d17a)

# Database
### UserData
|user_id | username | password| role| token | mu | sigma |
|--- | --- | --- | --- | --- | --- | --- |
| int | str | str | str/UserRole, optional | str | float, optional | float, optional | 

* `add`
* `remove`
* `is_verified`
* `get_user_id`
* `get_matchmaking_parameters`
* `set_matchmaking_parameters`

### GameData
|game_id | user1 | user2 | score1 | score2 | start_time | end_state | winner | disconnected|
|--- | --- | --- | --- | ---- | --- | --- | --- | ---|
|GameID (UUID) | int | int | float | float | str, optional | GameEndState | int | int |

* `add` 
* `remove` 

# Matchmaking
## Principle
* Each player get's a rating consisting (mainly) of:
  * a $\mu$ (`mu`) value: The average performance of the player
  * a $\sigma$ (`sigma`) value: The uncertainty of the skill
* ratings are used to predict outcomes of a game
* updated after a game

## Functionality

* Agents joining are put in the queue
* Fix percentage of online players are always waiting in queue
* Every few seconds matchmaking is updated and possible matches are formed
* match is suitable if:
 $\textit{probability of a draw} + \textit{time bonus} > \textit{threshold}$
* $\textit{time bonus} = \textit{combined waiting time in min}\cdot \textit{0.1}$
* after a match `mu` and `sigma` are updated based on score


# Documentation

[Here](https://github.com/martius-lab/teamproject-competition-server/tree/main/documentation) a documentation that was generated with [pdoc](https://pdoc.dev). Open `documentation/comprl.html` to see this documentation.

# Coding conventions
This project follows the [Google-Styleguide](https://google.github.io/styleguide/)