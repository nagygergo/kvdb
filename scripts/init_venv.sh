
#!/bin/bash
# On ubuntu distros ensurepip is not available.
python3.10 -m venv .venv --without-pip
source .venv/bin/activate
python ./get-pip.py
pip install pipenv
pipenv sync