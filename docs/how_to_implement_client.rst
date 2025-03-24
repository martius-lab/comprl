*************************
How to implement a client
*************************

For implementing a client, utilize the ``comprl.client`` package.

Create a class that inherits from :class:`comprl.client.Agent`.  The only required
implementation is the ``get_step()`` methods.  Additionally, you may override other
methods to receive and handle data about games being played or handle any errors that
may occur.

You can then use :func:`comprl.client.launch_client` to launch the client in a
standardized way.

A simple example can be found :ref:`below <example_hockey_client>`.


Client API
----------

.. autoclass:: comprl.client.Agent

   .. automethod:: run
   .. automethod:: get_step
   .. automethod:: is_ready
   .. automethod:: on_start_game
   .. automethod:: on_end_game
   .. automethod:: on_disconnect
   .. automethod:: on_message
   .. automethod:: on_error

.. autofunction:: comprl.client.launch_client


.. _example_hockey_client:

Example: Hockey client
----------------------

.. literalinclude:: ../comprl-hockey-agent/run_client.py


**Running the client:**

The client needs server URL, port and the users access token as arguments (handled by
:func:`comprl.client.launch_client`).  Any custom arguments of the agent can be passed
in the end using ``--args``:

.. code-block:: sh

    python3 ./client.py --server-url <URL> --server-port <PORT> \
        --token <YOUR ACCESS TOKEN> \
        --args --agent=strong

The server information can also be provided via environment variables, then they don't
need to be provided via the command line:

.. code-block:: sh

    # put this in your .bashrc or some other file that is sourced before running the agent
    export COMPRL_SERVER_URL=<URL>
    export COMPRL_SERVER_PORT=<PORT>
    export COMPRL_ACCESS_TOKEN=<YOUR ACCESS TOKEN>

Then just call

.. code-block:: sh

    python3 ./run_client.py --args --agent=strong
