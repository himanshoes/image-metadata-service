import json
import uuid
import boto3
import base64
import os
from boto3.dynamodb.conditions import Attr


# 1. Improved Client Setup
def get_client(service, is_resource=False):
    target = boto3.resource if is_resource else boto3.client

    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")

    kwargs = {
        "region_name": region,
        "aws_access_key_id": "test",
        "aws_secret_access_key": "test"
    }

    if os.environ.get("LOCALSTACK_HOSTNAME"):
        kwargs["endpoint_url"] = f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"
    else:
        kwargs["endpoint_url"] = "http://localhost:4566"

    return target(service, **kwargs)


# Initialize Resources
s3 = get_client('s3')
db = get_client('dynamodb', is_resource=True)
table = db.Table('ImageMetadata')
BUCKET_NAME = 'instagram-images'  # <--- Make sure this is here!


def lambda_handler(event, context):
    method = event.get('httpMethod')
    path = event.get('path', '')

    try:
        if path == "/images" and method == "POST":
            return upload(event)
        elif path == "/images" and method == "GET":
            return list_all(event)
        elif path.startswith("/images/") and method == "GET":
            return view(event)
        elif path.startswith("/images/") and method == "DELETE":
            return delete(event)
        return {"statusCode": 404, "body": json.dumps({"msg": "Not Found"})}
    except Exception as e:
        # 2. Add this print so you can see what's actually breaking!
        print(f"CRITICAL ERROR: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def upload(event):
    body = json.loads(event['body'])
    img_id = str(uuid.uuid4())
    metadata = body.get('metadata', {})

    # Task 1.1: S3 Upload - Using BUCKET_NAME from global scope
    s3.put_object(Bucket=BUCKET_NAME, Key=f"{img_id}.jpg", Body=base64.b64decode(body['image_base64']))

    # Task 1.1: DynamoDB Metadata
    table.put_item(Item={
        'ImageId': img_id,
        'UserId': metadata.get('user_id'),
        'Tags': metadata.get('tags', []),
        'Timestamp': metadata.get('timestamp')
    })
    return {"statusCode": 201, "body": json.dumps({"imageId": img_id})}


def list_all(event):
    q = event.get('queryStringParameters') or {}
    user, tag = q.get('user_id'), q.get('tag')
    filt = None
    if user: filt = Attr('UserId').eq(user)
    if tag:
        tag_f = Attr('Tags').contains(tag)
        filt = filt & tag_f if filt else tag_f
    res = table.scan(FilterExpression=filt) if filt else table.scan()
    return {"statusCode": 200, "body": json.dumps(res.get('Items', []))}


def view(event):
    img_id = event['path'].split('/')[-1]
    # Task 1.3: Generate Pre-signed URL
    url = s3.generate_presigned_url('get_object',
                                    Params={'Bucket': BUCKET_NAME, 'Key': f"{img_id}.jpg"},
                                    ExpiresIn=3600)
    return {"statusCode": 200, "body": json.dumps({"download_url": url})}


def delete(event):
    img_id = event['path'].split('/')[-1]
    s3.delete_object(Bucket=BUCKET_NAME, Key=f"{img_id}.jpg")
    table.delete_item(Key={'ImageId': img_id})
    return {"statusCode": 200, "body": json.dumps({"msg": "Deleted"})}