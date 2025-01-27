RL Competition Hockey Agent
===========================

This is a simple example implementation for a client of the comprl hockey game.  It
wraps an agent from the `hockey` package and implements a script to run it as a client
that connects to the comprl server.

To run the example agent, you first need to install the dependencies:
```
pip install -r ./requirements.txt
```

Then execute the script `run_client.py` to run the client:
```
python3 ./run_client.py --server-url <URL> --server-port <PORT> \
    --token <YOUR ACCESS TOKEN> \
    --args --agent=strong
```

The server information can also be provided via environment variables, then they don't
need to be provided via the command line:
```
# put this in your .bashrc or some other file that is sourced before running the agent
export COMPRL_SERVER_URL=<URL>
export COMPRL_SERVER_PORT=<PORT>
export COMPRL_ACCESS_TOKEN=<YOUR ACCESS TOKEN>
```
Then just call
```
python3 ./run_client.py --args --agent=strong
```


## The Auto-Restart Wrapper Script


`autostart.sh` is a wrapper script around `run_client.py`, that is meant to
automatically restart the client in case of infrequent issues like connection
hiccups or server restarts.  To use it simply replace `python3 ./run_client.py`
with `bash ./autorestart.sh` in the examples above.  Example:
```
bash ./autorestart.sh --server-url <URL> --server-port <PORT> \
    --token <YOUR ACCESS TOKEN> \
    --args --agent=strong
```

It keeps track of the number of restarts within a certain time window.  It will
stop if there are too many restarts (e.g. because an issue in the client
itself).  The length of the time window and the restart limit can be configured
via variables at the top of the script.

To stop the script, you need to press Ctrl+C twice.  Once to stop the client
and then again to stop the wrapper script.

You can enable notifications about restarts on ntfy.sh by setting a topic name
to `NTFY_TOPIC` at the top of the script.  Once set, open https://ntfy.sh/TOPIC
in your browser (or use the app on your phone) to get notified.
