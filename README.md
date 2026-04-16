# Instagram Metadata Service

A scalable, serverless backend for managing image uploads and metadata using **AWS Lambda, API Gateway, S3, and DynamoDB**. Developed for local testing using **LocalStack**.

## 🚀 Features
* **Automated Provisioning:** One-command infrastructure setup via `docker-compose`.
* **Serverless Architecture:** Event-driven logic using Python 3.8.
* **Metadata Management:** Fast retrieval and filtering using DynamoDB.
* **Secure Access:** Time-limited pre-signed URLs for image viewing.

## 🛠 Prerequisites
* Docker & Docker Compose
* Python 3.8+
* AWS CLI & `awslocal` wrapper

## 🏗 Setup & Execution

### 1. Configuration
This project uses environment variables to handle sensitive data such as the LocalStack Auth Token. 
* Create a `.env` file in the root directory.
* Add your token to the file:
  ```text
  LOCALSTACK_AUTH_TOKEN=your_actual_token_here