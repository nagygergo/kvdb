${BASH_SOURCE%/*}/start_server.sh > /dev/null 2>&1 &
process_id=$!
sleep 2
cd "${BASH_SOURCE%/*}/.."
locust -f load_tests/locustfile.py --headless -u 50  -r 2 --run-time 20
kill $process_id