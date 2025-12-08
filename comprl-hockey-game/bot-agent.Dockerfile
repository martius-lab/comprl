FROM server_image

WORKDIR /agent

# Add the code to run the bot clients
COPY ./comprl-hockey-agent .

USER comprl
# add a sleep here so that when starting everything together, the server gets a
# head-start before the bots are trying to connect.
CMD sleep 5; python ./run_client.py --args --agent "${AGENT_TYPE}"
