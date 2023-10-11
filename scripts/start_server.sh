source "${BASH_SOURCE%/*}/../.venv/bin/activate"
cd "${BASH_SOURCE%/*}/../"
python -B -m kvdb -t "127.0.0.1" -p 1025 -l 4