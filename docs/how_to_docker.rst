**************************************************
How to run the server + web interface using Docker
**************************************************

The CompRL repository contains an implementation of a simply "hockey" game, included in the `comprl-hockey-game` folder.  This also contains a Docker compose config for running the game server in a container.
Further, the `comprl-web-reflex` folder contains Docker compose files for running the web interface in containers.

**Note:** Currently the Docker setup for the web interface has some paths hard-coded for the hockey game, so when used for another game, the compose.yaml needs to be adjusted.

Some manual setup is needed to get things running:

1. Clone the comprl repo
2. Set `o+w` permissions for the `comprl-hockey-game` folder and the `hockey.db` file (TODO needs to be initialised first!)
3. Create a file `.env` somewhere with the following content:
   ```
   COMPRL_DATA_PATH=/path/to/game/save/directory
   DOMAIN=your.server-domain.com
   ```
   Create symlinks to that file in both `comprl-hockey-game` and `comprl-web-reflex`.
4. Make sure the directory specified above exists and has `o+w` permissions.
5. Adjust configuration to your needs in `comprl-hockey-game/config-docker.toml`
6. Start the game server by running
   ```
   sudo make up
   ```
   in `comprl-hockey-game`
7. Start the web server by running
   ```
   sudo make up
   ```
   in `comprl-web-reflex`

Both can be stopped again by running `sudo make down` in both directories.
