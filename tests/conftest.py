import pytest
import boto3
import os


@pytest.fixture(autouse=True)
def aws_env_setup():
    """Ensure tests use dummy credentials and point to LocalStack."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["TABLE_NAME"] = "ImageMetadata"
    os.environ["BUCKET_NAME"] = "instagram-images"
