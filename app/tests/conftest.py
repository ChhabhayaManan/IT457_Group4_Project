import os

# Skip the EC2 metadata lookup (and its timeout) when tests import the app.
os.environ.setdefault("INSTANCE_ID", "i-test")
