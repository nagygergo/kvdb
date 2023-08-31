source "${BASH_SOURCE%/*}/../.venv/bin/activate"

echo "=== Run flake8 for kvdb ==="
flake8 "${BASH_SOURCE%/*}/../kvdb"

echo "=== Run pylint for kvdb ==="
pylint "${BASH_SOURCE%/*}/../kvdb"

echo "=== Run flake8 for kvdb ==="
flake8 "${BASH_SOURCE%/*}/../tests"

echo "=== Run pylint for kvdb ==="
pylint "${BASH_SOURCE%/*}/../tests"