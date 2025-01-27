#!/bin/bash
# Wrapper script for run_client.py that automatically restarts the client if it
# terminates.
# It keeps track of the number of restarts and aborts if there are too many
# within a certain time window (see variables below).
# Comprl server information can either be set as environment variables below or
# be passed as arguments to this script (any arguments will simply be forwarded
# to run_client.py).
#
# NOTE: If you want to stop the script, you need to press Ctrl+C twice.  Once
# to stop the client and then again to stop the wrapper script.


# Keep track of restarts within this time window
THRESHOLD_TIME_WINDOW=600  # 10 min
# Threshold for the number of restarts in the time window
THRESHOLD=10

# If you set a topic name here, restart notifications will be sent to
# ntfy.sh/$NFTY_TOPIC (so you can more easily monitor if there are problems).
NTFY_TOPIC=

# You may set the server information here, then you don't need to pass it as
# argument.
# export COMPRL_SERVER_URL=<URL>
# export COMPRL_SERVER_PORT=<PORT>
# export COMPRL_ACCESS_TOKEN=<YOUR ACCESS TOKEN>

# Array to hold timestamps of terminations
termination_times=()

while true; do
    # Run the command foobar
    python3 ./run_client.py "$@"

    # Get the current timestamp
    current_time=$(date +%s)

    # Add the current timestamp to the termination times array
    termination_times+=("$current_time")

    # Remove timestamps outside of the time window
    termination_times=($(for time in "${termination_times[@]}"; do
        if (( current_time - time <= ${THRESHOLD_TIME_WINDOW} )); then
            echo "$time"
        fi
    done))

    # Check if the number of terminations exceeds the threshold
    if (( ${#termination_times[@]} > ${THRESHOLD} )); then
        echo
        echo "##############################################"
        echo "Restarted too many times within the last ${THRESHOLD_TIME_WINDOW} seconds."

        if [ -n "${NTFY_TOPIC}" ]; then
            curl -H "Priority: urgent" -H "Tags: warning" \
                -d "Too many restarts within the last ${THRESHOLD_TIME_WINDOW}" \
                ntfy.sh/${NTFY_TOPIC}
        fi

        exit 1
    fi

    # Wait a bit before restarting.  In case the client terminated due to a
    # server restart, it will take some time before the server is ready again.
    sleep 20

    echo
    echo "##############################################"
    echo "#                Restarting                  #"
    echo "##############################################"
    echo

    if [ -n "${NTFY_TOPIC}" ]; then
        curl -d "Restarting" ntfy.sh/${NTFY_TOPIC}
    fi
done

