# Install cdk cli
npm install -g aws-cdk

# Configure AWS access

* Configure profile
* Add this profile to test_lambdas.py script under `PROFILE` variable

# Install python packages
pip3 install -r requirements.txt

# Run tests
With parallelization:
`pytest -n 2 --durations=0 test_lambdas.py`

Without:
`pytest --durations=0 test_lambdas.py`