#!/bin/bash
# Set the region to match your docker-compose
export AWS_DEFAULT_REGION=us-west-2

echo "########### Creating S3 Bucket ###########"
# Create bucket and wait for it to exist
awslocal s3 mb s3://instagram-images
awslocal s3api wait bucket-exists --bucket instagram-images

echo "########### Creating DynamoDB ###########"
awslocal dynamodb create-table \
    --table-name ImageMetadata \
    --attribute-definitions AttributeName=ImageId,AttributeType=S \
    --key-schema AttributeName=ImageId,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

echo "########### Packaging & Creating Lambda ###########"
cd /usr/src/app
rm -f /tmp/function.zip
zip -r /tmp/function.zip .

awslocal lambda create-function \
    --function-name instagram-service \
    --runtime python3.8 \
    --handler handler.lambda_handler \
    --zip-file fileb:///tmp/function.zip \
    --role arn:aws:iam::000000000000:role/lambda-role


# 5. Create API Gateway
echo "########### Configuring API Gateway ###########"
API_ID=$(awslocal apigateway create-rest-api --name 'InstaAPI' --query 'id' --output text)
ROOT_ID=$(awslocal apigateway get-resources --rest-api-id $API_ID --query 'items[0].id' --output text)

# Create {proxy+} resource to handle all paths under /images
RES_ID=$(awslocal apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part '{proxy+}' \
    --query 'id' --output text)

# Attach ANY method to the proxy resource
awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method ANY \
    --authorization-type "NONE"

# Integrate API Gateway with the Lambda function
awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-west-2:lambda:path/2015-03-31/functions/arn:aws:lambda:us-west-2:000000000000:function:instagram-service/invocations

# Deploy the API to a 'prod' stage
awslocal apigateway create-deployment --rest-api-id $API_ID --stage-name prod

echo "########### Infrastructure Created Successfully ###########"
echo "API_ID: $API_ID"
echo "API Endpoint: http://localhost:4566/restapis/$API_ID/prod/_user_request_/images"