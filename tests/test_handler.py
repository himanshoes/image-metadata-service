import json
import base64
import pytest
from unittest.mock import patch, MagicMock
from src.handler import lambda_handler

# Mock data for reuse
FAKE_IMAGE_ID = "test-uuid-12345"


@pytest.fixture
def mock_boto():
    """Fixture to mock S3 and DynamoDB clients globally for tests."""
    with patch('src.handler.s3') as mock_s3, \
            patch('src.handler.table') as mock_table:
        yield mock_s3, mock_table


## --- Success Scenarios ---

def test_upload_image_success(mock_boto):
    """Task 1.1: Verify successful upload and metadata storage."""
    mock_s3, mock_table = mock_boto
    image_payload = base64.b64encode(b"fake-image-binary").decode('utf-8')

    event = {
        "path": "/images",
        "httpMethod": "POST",
        "body": json.dumps({
            "image_base64": image_payload,
            "metadata": {"user_id": "himanshu", "tags": ["bengaluru", "tech"]}
        })
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "imageId" in body
    mock_s3.put_object.assert_called_once()
    mock_table.put_item.assert_called_once()


def test_list_images_with_tag_filter(mock_boto):
    """Task 1.2: Verify listing works with query parameters."""
    _, mock_table = mock_boto
    mock_table.scan.return_value = {"Items": [{"ImageId": "1", "Tags": ["tech"]}]}

    event = {
        "path": "/images",
        "httpMethod": "GET",
        "queryStringParameters": {"tag": "tech"}
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    items = json.loads(response["body"])
    assert len(items) == 1
    assert items[0]["Tags"] == ["tech"]


def test_view_image_presigned_url(mock_boto):
    """Task 1.3: Verify pre-signed URL is generated for a specific ID."""
    mock_s3, _ = mock_boto
    mock_s3.generate_presigned_url.return_value = "http://localhost:4566/signed-url"

    event = {
        "path": f"/images/{FAKE_IMAGE_ID}",
        "httpMethod": "GET"
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert "download_url" in json.loads(response["body"])
    mock_s3.generate_presigned_url.assert_called_with(
        'get_object',
        Params={'Bucket': 'instagram-images', 'Key': f"{FAKE_IMAGE_ID}.jpg"},
        ExpiresIn=3600
    )


def test_delete_image_success(mock_boto):
    """Task 1.4: Verify both S3 and DynamoDB entries are removed."""
    mock_s3, mock_table = mock_boto

    event = {
        "path": f"/images/{FAKE_IMAGE_ID}",
        "httpMethod": "DELETE"
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    mock_s3.delete_object.assert_called_once()
    mock_table.delete_item.assert_called_once()

## --- Edge Cases & Error Handling ---

def test_handler_404_not_found():
    """Verify that unsupported paths or methods return 404."""
    event = {
        "path": "/unknown-route",
        "httpMethod": "POST"
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 404


def test_upload_missing_body():
    """Verify 500 error handling if body is missing in POST."""
    event = {
        "path": "/images",
        "httpMethod": "POST",
        "body": None
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 500
    assert "error" in json.loads(response["body"])