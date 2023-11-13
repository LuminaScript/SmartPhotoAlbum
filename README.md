# Photo Album Web Application

## Overview
This project implements a photo album web application that can be searched using natural language through both text and voice. It leverages AWS services such as Lex, OpenSearch, and Rekognition to create an intelligent search layer for querying photos based on various attributes like people, objects, actions, landmarks, and more.

## 1. API Gateway
The API Gateway serves as the entry point for the frontend application to interact with AWS services. It routes requests to the appropriate Lambda functions and handles responses.

### Features
- **PUT /photos**: Allows direct upload of photos to an S3 bucket. Utilizes S3 Proxy integration.
- **GET /search?q={query text}**: Connects to the search Lambda function to fetch search results based on natural language queries.

## 2. Lambda Functions
Lambda functions are used for indexing and searching photos within the application.

### Indexing Lambda (LF1)
- Triggered on S3 PUT event.
- Detects labels in the image using Rekognition and indexes them in OpenSearch.
- Handles metadata and custom labels.

### Search Lambda (LF2)
- Disambiguates search queries using Amazon Lex.
- Searches the indexed photos in OpenSearch and returns relevant results.

## 3. Frontend & S3
The frontend is a simple web application allowing users to search for photos, display results, and upload new photos with custom labels.

### Features
- Integration with API Gateway for search and upload functionality.
- Voice search capability using Amazon Transcribe.
- Hosted on S3 with static website hosting configuration.

## 4. CloudFormation
AWS CloudFormation is used to define and provision the AWS infrastructure required for the application.

### Template (T1)
- Represents all infrastructure resources (Lambdas, OpenSearch, API Gateway, etc.).
- Includes necessary IAM policies and roles for permissions.
