import boto3
import json
import base64
from botocore.httpsession import URLLib3Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session
from botocore.vendored import requests as botocore_requests  # Deprecated in newer versions

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')
s3_client = boto3.client('s3')

host = 'https://search-photos-vygvnrzj3wvay3jylfm7lpddzm.us-east-1.es.amazonaws.com'  # Use HTTPS
global_index = 'photos'


def lambda_handler(event, context):
    print("event: ")
    print(event)
    
    last_user_kw = event.get('q', '')
    object_key = last_user_kw + ".jpeg"
    print(last_user_kw)
    
    last_user_message = "show me " + last_user_kw
    
    
    print(f"Message from frontend: {last_user_message}")

    response = client.recognize_text(
        botId='IB30OVP5XI',
        botAliasId='CWWA5Q3QG7',
        localeId='en_US',
        sessionId='test_user-1i23y',
        text=last_user_message
    )

    print("response: ", json.dumps(response))
    
    # Extracting keywords from the Lex response
    keywords = []
    if "interpretations" in response:
        for interpretation in response["interpretations"]:
            intent = interpretation.get("intent", {})
            slots = intent.get("slots", {})
            for slot_key, slot_value in slots.items():
                # Assuming keywords are in 'resolvedValues' or 'interpretedValue'
                if "value" in slot_value:
                    value = slot_value["value"]
                    if "resolvedValues" in value:
                        keywords.extend(value["resolvedValues"])
                    elif "interpretedValue" in value:
                        keywords.append(value["interpretedValue"])

    # keywords = [w.capitalize() for w in keywords]
    print("Keywords extracted:", keywords)
    
    
    keyword_two=None
    search=""
    keyword_one = keywords[0].capitalize()
    search=search+keyword_one
    print ("keyword: ", keyword_one)
    print ("final search word: ", search)
    
    
    
    query = {"size":1000 ,"query": {"match": {"labels":keyword_one}}}
    query_json = json.dumps(query)  # Ensure the query is properly serialized as a JSON string
    
    session = get_session()
    request = AWSRequest(method="GET", url=host + '/' + global_index + '/_search',
                         data=query_json, headers={"Content-Type": "application/json"})
    SigV4Auth(session.get_credentials(), 'es', 'us-east-1').add_auth(request)
    prepared_request = request.prepare()
    http_session = URLLib3Session()
    response = http_session.send(prepared_request)
    
    data = json.loads(response.text)
    print("opensearch return:")
    print(data)
    
    print("data")

    es=data["hits"]["hits"]
    res=[]
    for i in es:
        res.append(i["_source"]["objectKey"])
    print (res)
    files_json = json.dumps({"files":res})
    print("files_json: ", files_json)

    # Construct direct S3 URLs
    s3_urls = []
    for hit in data['hits']['hits']:
        print("here")
        s3_key = hit['_source']['objectKey']
        url = f"https://6998-photos-b2.s3.amazonaws.com/{s3_key}"
        s3_urls.append(url)

    return {
        'statusCode': 200,
        'body': json.dumps({'urls': s3_urls})
    }
