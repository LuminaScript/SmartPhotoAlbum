import json
import boto3
import http.client
import mimetypes
import base64
from datetime import datetime


def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    rekognition_client = boto3.client('rekognition')
    opensearch_domain_endpoint = "search-photos-vygvnrzj3wvay3jylfm7lpddzm.us-east-1.es.amazonaws.com"
    opensearch_index_name = "photos"

    try:
        for record in event['Records']:
            print("[lambda_handler] record: ", record)
            bucket_name = record['s3']['bucket']['name']
            print("[lambda_hander] bucket_name", bucket_name)
            object_key = record['s3']['object']['key']
            print("[lambda_hander] object_key", object_key)
            created_timestamp = record['eventTime']
            print("[lambda_hander] created_timestamp", created_timestamp)

            labels = detect_labels(rekognition_client, s3_client, bucket_name, object_key)

            print("[lambda_handler] labels: ", labels)
            custom_labels = get_custom_labels(s3_client, bucket_name, object_key)
            print("[lambda_handler] custom_labels: ", custom_labels)

            labels.extend(custom_labels)
            print("[lambda_handler] 1")
            store_in_opensearch(opensearch_domain_endpoint, opensearch_index_name, object_key, bucket_name, created_timestamp, labels)
            print("[lambda_handler] 2")
           
        response_body = {
            "message": "Successfully processed S3 event",
            "input": event
        }

        response = {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }

        return response

    except Exception as e:
        print(f"Error processing S3 event: {str(e)}")
        response_body = {
            "message": "Error processing S3 event",
            "error": str(e)
        }

        response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/base64',
                'Access-Control-Allow-Headers': 'Content-Type,x-amz-meta-customLabels,x-api-key',
                'Access-Control-Allow-Origin': '*',  # Specify your domain instead of '*' for security reasons
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(response_body)
        }

        return response


def detect_labels(rekognition_client, s3_client, bucket_name, object_key):
    try:
        # Fetch the image from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key) # usage ??
        print("Response: ", response)
        image_bytes = response['Body'].read()
        base_64_binary = base64.decodebytes(image_bytes)

        # Use the 'Bytes' field to send image data for Rekognition processing
        rekog_response = rekognition_client.detect_labels(
            Image={
                'Bytes': base_64_binary
            }
        )
        labels = [label['Name'] for label in rekog_response['Labels']]
        print("Labels from rekog_response suggestions:", labels)
        return labels

    except Exception as e:
        print(f"Error in detect_labels: {str(e)}")
        return []


def get_custom_labels(s3_client, bucket_name, object_key):
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        custom_labels = response.get('Metadata', {}).get('x-amz-meta-customLabels', '').split(',')
        return custom_labels
    except Exception as e:
        print(f"Error retrieving custom labels: {str(e)}")
        return []

def store_in_opensearch(opensearch_domain_endpoint, opensearch_index_name, object_key, bucket_name, created_timestamp, labels):
    # Ensure index name is lowercase and does not start with invalid characters
    opensearch_index_name = opensearch_index_name.lower()
    print("[opensearch_index_name]: ",opensearch_index_name)
    
    photo_data = {
        "objectKey": object_key,
        "bucket": bucket_name,
        "createdTimestamp": created_timestamp,
        "labels": labels
    }
    print("object_key: ", object_key)
    opensearch_endpoint = f"/{opensearch_index_name}/_doc/{object_key}"

    
    conn = http.client.HTTPSConnection(opensearch_domain_endpoint)

    username = "master"
    password = "Zhang1998!"
    credentials = f"{username}:{password}"
    credentials_base64 = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    print("[store_in_opensearch] 5")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {credentials_base64}'
    }

    json_data = json.dumps(photo_data)
    print("[store_in_opensearch] photo_json_data: ", json_data)
    conn.request("PUT", opensearch_endpoint, json_data, headers)

    response = conn.getresponse()
    print("[store_in_opensearch] response: ", response)
    # if response.status != 201 or response.status != 200:
    #     print(f"Failed to index data in OpenSearch. Status code: {response.status}")
