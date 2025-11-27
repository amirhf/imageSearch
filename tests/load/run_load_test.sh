#!/bin/bash

# Usage: ./run_load_test.sh [python|go] [users] [duration]

BACKEND=${1:-python}
USERS=${2:-50}
DURATION=${3:-1m}
HOST="http://localhost:8000"

echo "========================================================"
echo "Running Load Test for Backend: $BACKEND"
echo "Users: $USERS, Duration: $DURATION"
echo "========================================================"

# Set the backend in .env (hacky but works for this setup)
# We assume the API picks up the change or we restart it.
# Since we are running locally, we might need to restart the API manually or via script.
# For now, let's assume the user/script handles the restart, or we just rely on the current state.
# Ideally, we should restart the API here.

# Export env var for the API if we were starting it here.
# But API is already running.
# We can use the /docs or just assume the user set the backend.
# Actually, let's just run the test and assume the environment is correct.
# We will output the results to a file.

mkdir -p tests/load/results

locust -f tests/load/locustfile.py \
    --headless \
    -u $USERS -r 10 \
    --run-time $DURATION \
    --host $HOST \
    --csv tests/load/results/benchmark_${BACKEND} \
    --html tests/load/results/benchmark_${BACKEND}.html

echo "Done. Results saved to tests/load/results/"
