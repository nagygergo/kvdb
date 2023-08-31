source "${BASH_SOURCE%/*}/../.venv/bin/activate"
coverage run -m pytest "${BASH_SOURCE%/*}/../tests"
coverage report -m